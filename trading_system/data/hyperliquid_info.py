from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from time import time

import httpx

from trading_system.data.sentiment import ExternalSentimentClient
from trading_system.data.universe import UniverseMetrics, select_top_liquid_markets
from trading_system.features.funding import funding_momentum, funding_persistence
from trading_system.features.orderflow import TradeFlowStore
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
    return max(
        _to_float(context.get("openInterestUsd")),
        _to_float(context.get("openInterest")),
        _to_float(context.get("dayNtlVlm")),
        _to_float(context.get("dayBaseVlm")),
    )


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
                rates.update(_find_predicted_rates(value))
    elif isinstance(payload, list):
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            symbol = str(entry.get("coin") or entry.get("name") or entry.get("symbol") or "")
            if not symbol:
                continue
            venue_map: dict[str, float] = {}
            for key, value in entry.items():
                if isinstance(value, dict):
                    for venue, rate in value.items():
                        venue_map[str(venue).lower()] = _to_float(rate)
                elif key.lower() in {"hl", "hyperliquid", "binance", "bybit"}:
                    venue_map[key.lower()] = _to_float(value)
            if venue_map:
                rates[symbol] = venue_map
    return rates


@dataclass(frozen=True)
class LiveSnapshot:
    universe: list[UniverseMetrics]
    markets: list[MarketFeatures]


class HyperliquidInfoClient:
    def __init__(
        self,
        base_url: str,
        flow_store: TradeFlowStore | None = None,
        sentiment_client: ExternalSentimentClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.flow_store = flow_store or TradeFlowStore()
        self.sentiment_client = sentiment_client or ExternalSentimentClient()

    async def _post_info(self, client: httpx.AsyncClient, payload: dict[str, object]) -> object:
        response = await client.post(f"{self.base_url}/info", json=payload)
        response.raise_for_status()
        return response.json()

    async def fetch_market_snapshot(
        self,
        oi_history,
        top_n: int = 50,
        include_external_sentiment: bool = True,
        use_trade_stream: bool = True,
    ) -> LiveSnapshot:
        async with httpx.AsyncClient(timeout=15.0) as client:
            meta_payload = await self._post_info(client, {"type": "metaAndAssetCtxs"})
            try:
                predicted_payload = await self._post_info(client, {"type": "predictedFundings"})
            except httpx.HTTPError:
                predicted_payload = {}

            meta, asset_contexts = self._split_meta_payload(meta_payload)
            predicted_rates = _find_predicted_rates(predicted_payload)
            history = oi_history.snapshot()

            universe_candidates: list[UniverseMetrics] = []
            symbol_to_context: dict[str, tuple[dict[str, object], dict[str, object]]] = {}

            for asset, context in zip(meta, asset_contexts, strict=False):
                symbol = str(asset.get("name") or asset.get("coin") or "")
                if not symbol:
                    continue
                symbol_to_context[symbol] = (asset, context)
                volume_24h = max(_to_float(context.get("dayNtlVlm")), _to_float(context.get("dayBaseVlm")))
                universe_candidates.append(
                    UniverseMetrics(
                        symbol=symbol,
                        volume_24h=volume_24h,
                        top_of_book_depth_usd=_book_depth_from_ctx(context),
                        spread_bps=self._spread_bps(context),
                        open_interest_usd=max(
                            _to_float(context.get("openInterestUsd")),
                            _to_float(context.get("openInterest")),
                        ),
                    )
                )

            top_universe = select_top_liquid_markets(universe_candidates, limit=top_n)
            top_symbols = [market.symbol for market in top_universe]
            top_volume = max((market.volume_24h for market in top_universe), default=1.0)
            long_short_ratios = await self._fetch_sentiment_map(client, top_symbols, include_external_sentiment)

        markets: list[MarketFeatures] = []
        now_ms = int(time() * 1000.0)
        for symbol in top_symbols:
            asset, context = symbol_to_context[symbol]
            historical_oi = history.get(symbol, [])
            open_interest = max(_to_float(context.get("openInterestUsd")), _to_float(context.get("openInterest")))
            oi_series = historical_oi + [open_interest]
            oi_zscore = oi_history.push(symbol, open_interest)

            funding_series = self._build_funding_series(context)
            current_funding = funding_series[-1] if funding_series else _to_float(context.get("funding"))
            predicted = self._predicted_rate_for_symbol(predicted_rates, symbol, "hyperliquid", fallback=current_funding)
            mid_price = self._mid_price(context)
            atr = max(mid_price * 0.008, _to_float(context.get("markPx")) * 0.008)
            ma_fast = simple_moving_average(self._build_price_series(context, mid_price, length=6))
            ma_slow = simple_moving_average(self._build_price_series(context, mid_price, length=21))

            real_cvd = self.flow_store.cvd(symbol) if use_trade_stream else 0.0
            real_cvd_delta = self.flow_store.cvd_delta(symbol) if use_trade_stream else 0.0
            imbalance_ratio = self.flow_store.imbalance_ratio(symbol) if use_trade_stream else 0.5
            market_age_ms = self.flow_store.last_trade_age_ms(symbol, now_ms) if use_trade_stream else 0
            liquidity_score = min(
                1.0,
                (
                    max(_to_float(context.get("dayNtlVlm")), 1.0) / max(top_volume, 1.0)
                ),
            )

            markets.append(
                MarketFeatures(
                    symbol=symbol,
                    mid_price=mid_price,
                    spread_bps=self._spread_bps(context),
                    volume_24h=max(_to_float(context.get("dayNtlVlm")), _to_float(context.get("dayBaseVlm"))),
                    liquidity_score=liquidity_score,
                    current_funding_1h=current_funding,
                    predicted_funding=predicted,
                    funding_persistence=funding_persistence(funding_series, threshold=0.0001),
                    funding_momentum=funding_momentum(funding_series, lookback=3),
                    microstructure_momentum=(predicted - current_funding) + ((imbalance_ratio - 0.5) * 0.0006),
                    open_interest=open_interest,
                    oi_zscore=oi_zscore,
                    oi_delta=self._oi_delta(oi_series),
                    cvd=real_cvd,
                    cvd_delta=real_cvd_delta,
                    long_short_ratio=long_short_ratios.get(symbol, 0.5),
                    hl_predicted_funding=predicted,
                    binance_predicted_funding=self._predicted_rate_for_symbol(predicted_rates, symbol, "binance", fallback=predicted),
                    bybit_predicted_funding=self._predicted_rate_for_symbol(predicted_rates, symbol, "bybit", fallback=predicted),
                    atr=atr,
                    atr_pct=atr_percent(atr, mid_price),
                    ma_fast=ma_fast,
                    ma_slow=ma_slow,
                    timestamp_ms=int(_to_float(context.get("time"), time() * 1000.0)),
                    size_decimals=int(asset.get("szDecimals", 3)),
                    flow_imbalance=imbalance_ratio,
                    trade_stream_fresh=(market_age_ms is None or market_age_ms <= 120_000) if use_trade_stream else True,
                )
            )

        ordered_markets = sorted(markets, key=lambda market: market.volume_24h, reverse=True)
        ordered_universe = [market for market in top_universe if market.symbol in {row.symbol for row in ordered_markets}]
        return LiveSnapshot(universe=ordered_universe, markets=ordered_markets)

    async def _fetch_sentiment_map(
        self,
        client: httpx.AsyncClient,
        symbols: list[str],
        enabled: bool,
    ) -> dict[str, float]:
        if not enabled:
            return {symbol: 0.5 for symbol in symbols}
        ratios = await gather_ratios(self.sentiment_client, client, symbols)
        return {symbol: ratio for symbol, ratio in zip(symbols, ratios, strict=False)}

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
        for key in ("midPx", "markPx", "oraclePx"):
            candidate = _to_float(context.get(key))
            if candidate > 0:
                return candidate
        return 0.0

    def _spread_bps(self, context: dict[str, object]) -> float:
        bid = _to_float(context.get("bestBid") or context.get("bidPx"))
        ask = _to_float(context.get("bestAsk") or context.get("askPx"))
        mid = self._mid_price(context)
        if bid > 0 and ask > 0 and mid > 0:
            return ((ask - bid) / mid) * 10_000.0
        return 10.0

    def _build_funding_series(self, context: dict[str, object]) -> list[float]:
        candidates: list[float] = []
        for key in ("funding", "premium", "currentFunding"):
            value = _to_float(context.get(key))
            if value:
                candidates.append(value)
        if not candidates:
            candidates = [0.0]
        while len(candidates) < 8:
            candidates.insert(0, candidates[0] * 0.9)
        return candidates[-8:]

    def _build_price_series(self, context: dict[str, object], mid_price: float, length: int) -> list[float]:
        day_change = _to_float(context.get("dayNtlVlm")) / max(_to_float(context.get("openInterest")), 1.0)
        drift = min(day_change / 50.0, 0.03)
        return [mid_price * (1.0 - drift * (length - idx) / max(length, 1)) for idx in range(length)]

    def _oi_delta(self, oi_series: Iterable[float]) -> float:
        values = list(oi_series)
        if len(values) < 2 or values[-2] == 0:
            return 0.0
        return (values[-1] - values[-2]) / values[-2]


async def gather_ratios(
    sentiment_client: ExternalSentimentClient,
    client: httpx.AsyncClient,
    symbols: list[str],
) -> list[float]:
    import asyncio

    coros = [sentiment_client.long_short_ratio(client, symbol) for symbol in symbols]
    results = await asyncio.gather(*coros, return_exceptions=True)
    ratios: list[float] = []
    for result in results:
        if isinstance(result, Exception):
            ratios.append(0.5)
        else:
            ratios.append(float(result))
    return ratios
