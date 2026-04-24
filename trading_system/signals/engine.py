from trading_system.signals.models import MarketFeatures, StrategyType, TradeSignal
from trading_system.signals.scoring import (
    conviction_score,
    cross_exchange_alignment,
    funding_pressure,
    orderflow_pressure,
    positioning_pressure,
    trend_filter,
    weighted_score,
)


def _risk_pct(strength: float, liquidity_score: float) -> float:
    base = 0.0025 + max(0.0, strength - 0.70) / 0.25 * 0.0035
    liquidity_bonus = min(max(liquidity_score, 0.0), 1.0) * 0.0015
    return min(0.0075, base + liquidity_bonus)


def _tp_prices(side: str, mid_price: float, atr: float) -> tuple[float, float]:
    if side == "long":
        return (mid_price + 1.5 * atr, mid_price + 2.5 * atr)
    return (mid_price - 1.5 * atr, mid_price - 2.5 * atr)


def continuation_signal(features: MarketFeatures) -> TradeSignal | None:
    score = weighted_score(features)
    strength = conviction_score(features)
    funding_score = funding_pressure(features)
    positioning_score = positioning_pressure(features)
    orderflow_score = orderflow_pressure(features)
    alignment_score = cross_exchange_alignment(features)
    trend_score = trend_filter(features)

    if strength < 0.70 or features.spread_bps > 5:
        return None

    long_ok = (
        score > 0
        and features.predicted_funding > features.current_funding_1h
        and features.current_funding_1h > 0
        and features.oi_delta > 0
        and features.oi_zscore > 0
        and features.cvd_delta > 0
        and features.long_short_ratio > 0.55
        and features.funding_persistence >= 3
        and features.ma_fast >= features.ma_slow
    )
    short_ok = (
        score < 0
        and features.predicted_funding < features.current_funding_1h
        and features.current_funding_1h < 0
        and features.oi_delta < 0
        and features.oi_zscore < 0
        and features.cvd_delta < 0
        and features.long_short_ratio < 0.45
        and features.funding_persistence >= 3
        and features.ma_fast <= features.ma_slow
    )

    if long_ok:
        return TradeSignal(
            symbol=features.symbol,
            side="long",
            strategy=StrategyType.CONTINUATION,
            strength=strength,
            funding_score=funding_score,
            positioning_score=positioning_score,
            orderflow_score=orderflow_score,
            alignment_score=alignment_score,
            trend_score=trend_score,
            suggested_risk_pct=_risk_pct(strength, features.liquidity_score),
            reason="positive funding regime strengthening with rising OI, positive CVD, long crowd expansion, and MA trend support",
            invalidation_price=features.mid_price - 1.5 * features.atr,
            take_profit_prices=_tp_prices("long", features.mid_price, features.atr),
        )

    if short_ok:
        return TradeSignal(
            symbol=features.symbol,
            side="short",
            strategy=StrategyType.CONTINUATION,
            strength=strength,
            funding_score=funding_score,
            positioning_score=positioning_score,
            orderflow_score=orderflow_score,
            alignment_score=alignment_score,
            trend_score=trend_score,
            suggested_risk_pct=_risk_pct(strength, features.liquidity_score),
            reason="negative funding regime strengthening with rising short crowd pressure, negative CVD, and MA trend support",
            invalidation_price=features.mid_price + 1.5 * features.atr,
            take_profit_prices=_tp_prices("short", features.mid_price, features.atr),
        )

    return None


def mean_reversion_signal(features: MarketFeatures) -> TradeSignal | None:
    extreme_funding = abs(features.current_funding_1h) > 0.00025
    skewed_positioning = features.long_short_ratio > 0.70 or features.long_short_ratio < 0.30
    oi_weakening = (
        features.current_funding_1h > 0 and features.oi_delta <= 0
    ) or (
        features.current_funding_1h < 0 and features.oi_delta >= 0
    )
    cvd_divergence = (
        features.current_funding_1h > 0 and features.cvd_delta < 0
    ) or (
        features.current_funding_1h < 0 and features.cvd_delta > 0
    )
    funding_score = funding_pressure(features)
    positioning_score = positioning_pressure(features)
    orderflow_score = orderflow_pressure(features)
    alignment_score = cross_exchange_alignment(features)
    trend_score = trend_filter(features)
    strength = max(0.70, conviction_score(features) - 0.05)

    if not all([extreme_funding, skewed_positioning, oi_weakening, cvd_divergence]):
        return None

    if features.spread_bps > 5:
        return None

    if features.current_funding_1h > 0 and features.long_short_ratio > 0.75:
        return TradeSignal(
            symbol=features.symbol,
            side="short",
            strategy=StrategyType.MEAN_REVERSION,
            strength=strength,
            funding_score=funding_score,
            positioning_score=positioning_score,
            orderflow_score=orderflow_score,
            alignment_score=alignment_score,
            trend_score=trend_score,
            suggested_risk_pct=max(0.0025, _risk_pct(strength, features.liquidity_score) - 0.0010),
            reason="positive funding extreme with crowded longs, stalling OI growth, and bearish CVD divergence",
            invalidation_price=features.mid_price + 1.5 * features.atr,
            take_profit_prices=_tp_prices("short", features.mid_price, features.atr),
        )

    if features.current_funding_1h < 0 and features.long_short_ratio < 0.30:
        return TradeSignal(
            symbol=features.symbol,
            side="long",
            strategy=StrategyType.MEAN_REVERSION,
            strength=strength,
            funding_score=funding_score,
            positioning_score=positioning_score,
            orderflow_score=orderflow_score,
            alignment_score=alignment_score,
            trend_score=trend_score,
            suggested_risk_pct=max(0.0025, _risk_pct(strength, features.liquidity_score) - 0.0010),
            reason="negative funding extreme with crowded shorts, stalling OI growth, and bullish CVD divergence",
            invalidation_price=features.mid_price - 1.5 * features.atr,
            take_profit_prices=_tp_prices("long", features.mid_price, features.atr),
        )

    return None


def generate_signal(features: MarketFeatures) -> TradeSignal | None:
    return mean_reversion_signal(features) or continuation_signal(features)


def rank_trade_candidates(markets: list[MarketFeatures]) -> list[TradeSignal]:
    candidates = [signal for signal in (generate_signal(market) for market in markets) if signal]
    return sorted(candidates, key=lambda signal: signal.strength, reverse=True)
