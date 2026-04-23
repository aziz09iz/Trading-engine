from math import tanh
from statistics import mean

from trading_system.signals.models import MarketFeatures


def clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def funding_pressure(features: MarketFeatures) -> float:
    predicted_edge = features.predicted_funding - features.current_funding_1h
    persistence_boost = min(features.funding_persistence / 5.0, 1.0)
    raw = (predicted_edge * 10_000.0) + (features.funding_momentum * 5_000.0)
    return clamp(tanh(raw) * persistence_boost)


def oi_trend(features: MarketFeatures) -> float:
    return clamp(tanh(features.oi_delta * 5.0))


def cvd_strength(features: MarketFeatures) -> float:
    return clamp(tanh(features.cvd_delta / max(abs(features.cvd), 1.0)))


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


def weighted_score(features: MarketFeatures) -> float:
    return clamp(
        0.30 * funding_pressure(features)
        + 0.25 * oi_trend(features)
        + 0.25 * cvd_strength(features)
        + 0.20 * cross_exchange_alignment(features)
    )
