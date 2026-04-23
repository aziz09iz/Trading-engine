from trading_system.signals.models import MarketFeatures, StrategyType, TradeSignal
from trading_system.signals.scoring import weighted_score


def continuation_signal(features: MarketFeatures) -> TradeSignal | None:
    score = weighted_score(features)
    strength = abs(score)

    if strength < 0.70 or features.spread_bps > 5:
        return None

    long_ok = (
        score > 0
        and features.predicted_funding > features.current_funding_1h
        and features.oi_delta > 0
        and features.cvd_delta > 0
        and features.funding_persistence >= 3
    )
    short_ok = (
        score < 0
        and features.predicted_funding < features.current_funding_1h
        and features.oi_delta < 0
        and features.cvd_delta < 0
        and features.funding_persistence >= 3
    )

    if long_ok:
        return TradeSignal(
            symbol=features.symbol,
            side="long",
            strategy=StrategyType.CONTINUATION,
            strength=strength,
            reason="funding rising, OI expanding, CVD positive, persistent pressure",
            invalidation_price=features.mid_price - 1.5 * features.atr,
        )

    if short_ok:
        return TradeSignal(
            symbol=features.symbol,
            side="short",
            strategy=StrategyType.CONTINUATION,
            strength=strength,
            reason="funding falling, OI weakening, CVD negative, persistent pressure",
            invalidation_price=features.mid_price + 1.5 * features.atr,
        )

    return None


def mean_reversion_signal(features: MarketFeatures) -> TradeSignal | None:
    extreme_funding = abs(features.current_funding_1h) > 0.00025
    skewed_positioning = features.long_short_ratio > 0.75 or features.long_short_ratio < 0.25
    oi_weakening = features.oi_delta <= 0
    cvd_divergence = (
        features.current_funding_1h > 0 and features.cvd_delta < 0
    ) or (
        features.current_funding_1h < 0 and features.cvd_delta > 0
    )

    if not all([extreme_funding, skewed_positioning, oi_weakening, cvd_divergence]):
        return None

    if features.spread_bps > 5:
        return None

    if features.current_funding_1h > 0 and features.long_short_ratio > 0.75:
        return TradeSignal(
            symbol=features.symbol,
            side="short",
            strategy=StrategyType.MEAN_REVERSION,
            strength=0.80,
            reason="positive funding extreme with crowded longs and weakening flow",
            invalidation_price=features.mid_price + 1.5 * features.atr,
        )

    if features.current_funding_1h < 0 and features.long_short_ratio < 0.25:
        return TradeSignal(
            symbol=features.symbol,
            side="long",
            strategy=StrategyType.MEAN_REVERSION,
            strength=0.80,
            reason="negative funding extreme with crowded shorts and weakening flow",
            invalidation_price=features.mid_price - 1.5 * features.atr,
        )

    return None


def generate_signal(features: MarketFeatures) -> TradeSignal | None:
    return mean_reversion_signal(features) or continuation_signal(features)
