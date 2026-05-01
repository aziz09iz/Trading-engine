from __future__ import annotations

from dataclasses import dataclass
from time import time

import httpx


def _to_float(value: object, default: float = 0.5) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_binance_symbol(symbol: str) -> str | None:
    cleaned = symbol.replace("-", "").replace("/", "").upper()
    if not cleaned or cleaned.startswith("@") or cleaned.endswith("USDC"):
        return None
    if cleaned.endswith("USD"):
        cleaned = cleaned[:-3]
    aliases = {
        "XBT": "BTC",
        "UBTC": "BTC",
    }
    base = aliases.get(cleaned, cleaned)
    return f"{base}USDT"


@dataclass
class CachedSentiment:
    ratio: float
    updated_at: float


class ExternalSentimentClient:
    def __init__(self, ttl_seconds: int = 600) -> None:
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, CachedSentiment] = {}

    async def long_short_ratio(
        self,
        client: httpx.AsyncClient,
        symbol: str,
    ) -> float:
        exchange_symbol = to_binance_symbol(symbol)
        if exchange_symbol is None:
            return 0.5

        cached = self._cache.get(exchange_symbol)
        now = time()
        if cached is not None and (now - cached.updated_at) < self.ttl_seconds:
            return cached.ratio

        response = await client.get(
            "https://fapi.binance.com/futures/data/globalLongShortAccountRatio",
            params={
                "symbol": exchange_symbol,
                "period": "1h",
                "limit": 1,
            },
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list) and payload:
            latest = payload[-1]
            ratio = _to_float(latest.get("longShortRatio"), 1.0)
            long_account = _to_float(latest.get("longAccount"), 0.5)
            short_account = _to_float(latest.get("shortAccount"), 0.5)
            if long_account > 0 and short_account > 0:
                normalized = long_account / max(long_account + short_account, 1e-9)
            else:
                normalized = ratio / max(1.0 + ratio, 1e-9)
            normalized = max(0.05, min(0.95, normalized))
            self._cache[exchange_symbol] = CachedSentiment(ratio=normalized, updated_at=now)
            return normalized
        return cached.ratio if cached is not None else 0.5
