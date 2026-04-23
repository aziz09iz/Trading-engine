from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

Side = Literal["long", "short"]


class StrategyType(StrEnum):
    CONTINUATION = "continuation"
    MEAN_REVERSION = "mean_reversion"


@dataclass(frozen=True)
class MarketFeatures:
    symbol: str
    mid_price: float
    spread_bps: float
    current_funding_1h: float
    predicted_funding: float
    funding_persistence: int
    funding_momentum: float
    open_interest: float
    oi_delta: float
    cvd: float
    cvd_delta: float
    long_short_ratio: float
    hl_predicted_funding: float
    binance_predicted_funding: float
    bybit_predicted_funding: float
    atr: float
    timestamp_ms: int


@dataclass(frozen=True)
class TradeSignal:
    symbol: str
    side: Side
    strategy: StrategyType
    strength: float
    reason: str
    invalidation_price: float | None = None
