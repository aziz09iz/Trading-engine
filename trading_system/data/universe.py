from dataclasses import dataclass


@dataclass(frozen=True)
class UniverseMetrics:
    symbol: str
    volume_24h: float
    top_of_book_depth_usd: float
    spread_bps: float
    open_interest_usd: float


def liquidity_score(metrics: UniverseMetrics) -> float:
    spread_penalty = max(metrics.spread_bps, 0.25)
    return (
        0.45 * metrics.volume_24h
        + 0.30 * metrics.top_of_book_depth_usd
        + 0.20 * metrics.open_interest_usd
        + 0.05 * (1.0 / spread_penalty)
    )


def select_top_liquid_markets(
    markets: list[UniverseMetrics],
    limit: int = 10,
    max_spread_bps: float = 8.0,
) -> list[UniverseMetrics]:
    eligible = [market for market in markets if market.spread_bps <= max_spread_bps]
    if not eligible:
        eligible = markets
    return sorted(eligible, key=liquidity_score, reverse=True)[:limit]
