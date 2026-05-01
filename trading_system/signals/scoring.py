from math import tanh
from statistics import mean

from trading_system.signals.models import MarketFeatures


def clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def funding_pressure(features: MarketFeatures) -> float:
    predicted_edge = features.predicted_funding - features.current_funding_1h
    persistence_boost = min(features.funding_persistence / 4.0, 1.0)
    raw = (
        (features.current_funding_1h * 7_500.0)
        + (predicted_edge * 12_000.0)
        + (features.funding_momentum * 5_500.0)
        + (features.microstructure_momentum * 4_000.0)
    )
    return clamp(tanh(raw) * (0.65 + 0.35 * persistence_boost))


def positioning_pressure(features: MarketFeatures) -> float:
    crowd_skew = (features.long_short_ratio - 0.5) * 2.0
    oi_expansion = tanh(features.oi_delta * 5.0)
    oi_extreme = tanh(features.oi_zscore / 2.5)
    flow_skew = (features.flow_imbalance - 0.5) * 2.0
    return clamp(0.35 * crowd_skew + 0.30 * oi_expansion + 0.20 * oi_extreme + 0.15 * flow_skew)


def orderflow_pressure(features: MarketFeatures) -> float:
    flow_delta = tanh(features.cvd_delta / max(abs(features.cvd), 1.0))
    flow_level = tanh(features.cvd / 10_000_000.0)
    freshness_multiplier = 1.0 if features.trade_stream_fresh else 0.7
    return clamp((0.55 * flow_delta + 0.25 * flow_level + 0.20 * ((features.flow_imbalance - 0.5) * 2.0)) * freshness_multiplier)


def cross_exchange_alignment(features: MarketFeatures) -> float:
    rates = [
        features.hl_predicted_funding,
        features.binance_predicted_funding,
        features.bybit_predicted_funding,
    ]
    avg_rate = mean(rates)
    dispersion = max(rates) - min(rates)
    penalty = min(abs(dispersion) * 10_000.0, 0.5)
    return clamp(tanh(avg_rate * 10_000.0) * (1.0 - penalty))


def trend_filter(features: MarketFeatures) -> float:
    ma_gap = 0.0
    if features.mid_price > 0:
        ma_gap = (features.ma_fast - features.ma_slow) / features.mid_price

    atr_penalty = min(features.atr_pct * 8.0, 0.35)
    return clamp(tanh(ma_gap * 40.0) * (1.0 - atr_penalty))


def weighted_score(features: MarketFeatures) -> float:
    return clamp(
        0.30 * funding_pressure(features)
        + 0.25 * positioning_pressure(features)
        + 0.25 * orderflow_pressure(features)
        + 0.20 * cross_exchange_alignment(features)
    )


def conviction_score(features: MarketFeatures) -> float:
    raw = (
        0.28 * abs(funding_pressure(features))
        + 0.24 * abs(positioning_pressure(features))
        + 0.20 * abs(orderflow_pressure(features))
        + 0.16 * abs(cross_exchange_alignment(features))
        + 0.12 * abs(trend_filter(features))
    )
    liquidity_bonus = min(features.liquidity_score, 1.0) * 0.07
    spread_penalty = min(features.spread_bps / 8.0, 0.22)
    freshness_bonus = 0.04 if features.trade_stream_fresh else -0.03
    return clamp(raw + liquidity_bonus + freshness_bonus - spread_penalty, 0.0, 1.0)
