from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from time import time

import httpx

from trading_system.data.universe import UniverseMetrics, select_top_liquid_markets
from trading_system.features.funding import funding_momentum, funding_persistence
from trading_system.features.trend import atr_percent, simple_moving_average
from trading_system.signals.models import MarketFeatures


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _book_depth_from_ctx(context: dict[str, object]) -> float:
    for key in ("openInterestUsd", "openInterest", "dayNtlVlm", "dayBaseVlm"):
        if key in context:
            return _to_float(context.get(key))
    return 0.0


def _find_predicted_rates(payload: object) -> dict[str, dict[str, float]]:
    rates: dict[str, dict[str, float]] = {}
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, dict):
                venue_map = {
                    venue.lower(): _to_float(rate)
                    for venue, rate in value.items()
                    if isinstance(rate, (int, float, str))
                }
                if venue_map:
                    rates[str(key)] = venue_map
            elif isinstance(value, list):
                nested = _find_predicted_rates(value)
                if nested:
                    rates.update(nested)
    elif isinstance(payload, list):
        for entry in payload:
            if isinstance(entry, dict):
                symbol = str(entry.get("coin") or entry.get("name") or entry.get("symbol") or "")
                if not symbol:
                    continue
                venue_map: dict[str, float] = {}
                for key in ("Hl", "hl", "hyperliquid", "Hyperliquid", "Binance", "binance", "Bybit", "bybit"):
                    if key in entry:
                        venue_map[key.lower()] = _to_float(entry[key])
                for key, value in entry.items():
                    if isinstance(value, dict):
                        for venue, rate in value.items():
                            venue_map[str(venue).lower()] = _to_float(rate)
                if venue_map:
                    rates[symbol] = venue_map
    return rates


@dataclass(frozen=True)
class LiveSnapshot:
    universe: list[UniverseMetrics]
    markets: list[MarketFeatures]


class HyperliquidInfoClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def _post_info(self, client: httpx.AsyncClient, payload: dict[str, object]) -> object:
        response = await client.post(f"{self.base_url}/info", json=payload)
        response.raise_for_status()
        return response.json()

    async def fetch_market_snapshot(
        self,
        oi_history,
        top_n: int = 10,
    ) -> LiveSnapshot:
        async with httpx.AsyncClient(timeout=15.0) as client:
            meta_payload = await self._post_info(client, {"type": "metaAndAssetCtxs"})
            predicted_payload = await self._post_info(client, {"type": "predictedFundings"})

        meta, asset_contexts = self._split_meta_payload(meta_payload)
        predicted_rates = _find_predicted_rates(predicted_payload)
        history = oi_history.snapshot()

        universe_candidates: list[UniverseMetrics] = []
        symbol_to_context: dict[str, tuple[dict[str, object], dict[str, object]]] = {}

        for asset, context in zip(meta, asset_contexts, strict=False):
            symbol = str(asset.get("name") or asset.get("coin") or asset.get("szDecimals") or "")
            if not symbol:
                continue
            symbol_to_context[symbol] = (asset, context)
            spread_bps = self._spread_bps(context)
            volume_24h = max(_to_float(context.get("dayNtlVlm")), _to_float(context.get("dayBaseVlm")))
            universe_candidates.append(
                UniverseMetrics(
                    symbol=symbol,
                    volume_24h=volume_24h,
                    top_of_book_depth_usd=_book_depth_from_ctx(context),
                    spread_bps=spread_bps,
                    open_interest_usd=_to_float(context.get("openInterest")),
                )
            )

        top_universe = select_top_liquid_markets(universe_candidates, limit=top_n)
        top_symbols = {market.symbol for market in top_universe}
        top_volume = max((market.volume_24h for market in top_universe), default=1.0)

        markets: list[MarketFeatures] = []
        for symbol in top_symbols:
            asset, context = symbol_to_context[symbol]
            historical_oi = history.get(symbol, [])
            open_interest = _to_float(context.get("openInterest"))
            oi_series = historical_oi + [open_interest]
            oi_zscore = oi_history.push(symbol, open_interest)

            funding_series = self._build_funding_series(context)
            current_funding = funding_series[-1] if funding_series else _to_float(context.get("funding"))
            predicted = self._predicted_rate_for_symbol(predicted_rates, symbol, "hyperliquid", fallback=current_funding)
            mid_price = self._mid_price(context)
            atr = max(mid_price * 0.01, _to_float(context.get("markPx")) * 0.01)
            ma_fast = simple_moving_average(self._build_price_series(context, mid_price, length=5))
            ma_slow = simple_moving_average(self._build_price_series(context, mid_price, length=20))

            markets.append(
                MarketFeatures(
                    symbol=symbol,
                    mid_price=mid_price,
                    spread_bps=self._spread_bps(context),
                    volume_24h=max(_to_float(context.get("dayNtlVlm")), _to_float(context.get("dayBaseVlm"))),
                    liquidity_score=min(
                        1.0,
                        (
                            max(_to_float(context.get("dayNtlVlm")), 1.0) / max(top_volume, 1.0)
                        ),
                    ),
                    current_funding_1h=current_funding,
                    predicted_funding=predicted,
                    funding_persistence=funding_persistence(funding_series, threshold=0.0001),
                    funding_momentum=funding_momentum(funding_series, lookback=3),
                    microstructure_momentum=predicted - current_funding,
                    open_interest=open_interest,
                    oi_zscore=oi_zscore,
                    oi_delta=self._oi_delta(oi_series),
                    cvd=self._synthetic_cvd(context),
                    cvd_delta=self._synthetic_cvd_delta(context),
                    long_short_ratio=self._synthetic_long_short_ratio(context, current_funding, predicted, oi_zscore),
                    hl_predicted_funding=predicted,
                    binance_predicted_funding=self._predicted_rate_for_symbol(predicted_rates, symbol, "binance", fallback=predicted),
                    bybit_predicted_funding=self._predicted_rate_for_symbol(predicted_rates, symbol, "bybit", fallback=predicted),
                    atr=atr,
                    atr_pct=atr_percent(atr, mid_price),
                    ma_fast=ma_fast,
                    ma_slow=ma_slow,
                    timestamp_ms=int(_to_float(context.get("time"), time() * 1000.0)),
                    size_decimals=int(asset.get("szDecimals", 3)),
                )
            )

        ordered_markets = sorted(markets, key=lambda market: market.volume_24h, reverse=True)
        ordered_universe = [market for market in top_universe if market.symbol in {row.symbol for row in ordered_markets}]
        return LiveSnapshot(universe=ordered_universe, markets=ordered_markets)

    def _split_meta_payload(self, payload: object) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        if isinstance(payload, list) and len(payload) == 2:
            meta_block, contexts_block = payload
            universe = []
            if isinstance(meta_block, dict):
                universe = [asset for asset in meta_block.get("universe", []) if isinstance(asset, dict)]
            contexts = [ctx for ctx in contexts_block if isinstance(ctx, dict)] if isinstance(contexts_block, list) else []
            return universe, contexts
        return [], []

    def _predicted_rate_for_symbol(
        self,
        predicted_rates: dict[str, dict[str, float]],
        symbol: str,
        venue: str,
        fallback: float,
    ) -> float:
        payload = predicted_rates.get(symbol, {})
        if not payload:
            return fallback
        for key, value in payload.items():
            if venue in key.lower():
                return value
        return fallback

    def _mid_price(self, context: dict[str, object]) -> float:
        candidates = [
            _to_float(context.get("midPx")),
            _to_float(context.get("markPx")),
            _to_float(context.get("oraclePx")),
            _to_float(context.get("premium")),
        ]
        for candidate in candidates:
            if candidate > 0:
                return candidate
        return 0.0

    def _spread_bps(self, context: dict[str, object]) -> float:
        bid = _to_float(context.get("bestBid") or context.get("bidPx"))
        ask = _to_float(context.get("bestAsk") or context.get("askPx"))
        mid = self._mid_price(context)
        if bid > 0 and ask > 0 and mid > 0:
            return ((ask - bid) / mid) * 10_000.0
        return 2.0

    def _build_funding_series(self, context: dict[str, object]) -> list[float]:
        candidates: list[float] = []
        for key in ("funding", "premium", "currentFunding"):
            value = _to_float(context.get(key))
            if value:
                candidates.append(value)
        if not candidates:
            candidates = [0.0]
        while len(candidates) < 6:
            candidates.insert(0, candidates[0] * 0.95)
        return candidates[-6:]

    def _build_price_series(self, context: dict[str, object], mid_price: float, length: int) -> list[float]:
        day_change = _to_float(context.get("dayNtlVlm")) / max(_to_float(context.get("openInterest")), 1.0)
        drift = min(day_change / 50.0, 0.03)
        return [mid_price * (1.0 - drift * (length - idx) / max(length, 1)) for idx in range(length)]

    def _oi_delta(self, oi_series: Iterable[float]) -> float:
        values = list(oi_series)
        if len(values) < 2 or values[-2] == 0:
            return 0.0
        return (values[-1] - values[-2]) / values[-2]

    def _synthetic_cvd(self, context: dict[str, object]) -> float:
        funding = _to_float(context.get("funding"))
        volume = max(_to_float(context.get("dayNtlVlm")), 1.0)
        return funding * volume * 0.4

    def _synthetic_cvd_delta(self, context: dict[str, object]) -> float:
        funding = _to_float(context.get("funding"))
        predicted = _to_float(context.get("premium")) or funding
        volume = max(_to_float(context.get("dayNtlVlm")), 1.0)
        return (predicted - funding) * volume * 0.3

    def _synthetic_long_short_ratio(
        self,
        context: dict[str, object],
        current_funding: float,
        predicted: float,
        oi_zscore: float,
    ) -> float:
        skew = 0.5 + (current_funding * 400.0) + ((predicted - current_funding) * 600.0) + (oi_zscore * 0.04)
        return max(0.2, min(0.8, skew))
