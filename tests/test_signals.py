from trading_system.signals.engine import generate_signal
from trading_system.signals.models import MarketFeatures, StrategyType


def test_generates_continuation_long_signal() -> None:
    features = MarketFeatures(
        symbol="BTC",
        mid_price=100_000,
        spread_bps=1,
        volume_24h=2_000_000_000,
        liquidity_score=0.95,
        current_funding_1h=0.0001,
        predicted_funding=0.0005,
        funding_persistence=5,
        funding_momentum=0.0002,
        microstructure_momentum=0.00015,
        open_interest=1_000_000,
        oi_zscore=1.4,
        oi_delta=0.5,
        cvd=15_000_000,
        cvd_delta=4_000_000,
        long_short_ratio=0.72,
        hl_predicted_funding=0.0005,
        binance_predicted_funding=0.00045,
        bybit_predicted_funding=0.0004,
        atr=1_000,
        atr_pct=0.01,
        ma_fast=100_500,
        ma_slow=99_700,
        timestamp_ms=1,
        flow_imbalance=0.62,
        trade_stream_fresh=True,
    )

    signal = generate_signal(features)

    assert signal is not None
    assert signal.side == "long"
    assert signal.strategy == StrategyType.CONTINUATION
    assert signal.suggested_risk_pct > 0.005
    assert len(signal.take_profit_prices) == 2


def test_generates_mean_reversion_short_signal() -> None:
    features = MarketFeatures(
        symbol="ETH",
        mid_price=3_200,
        spread_bps=2,
        volume_24h=1_400_000_000,
        liquidity_score=0.90,
        current_funding_1h=0.00042,
        predicted_funding=0.00028,
        funding_persistence=6,
        funding_momentum=-0.0001,
        microstructure_momentum=-0.00012,
        open_interest=850_000_000,
        oi_zscore=2.1,
        oi_delta=-0.10,
        cvd=9_000_000,
        cvd_delta=-2_400_000,
        long_short_ratio=0.82,
        hl_predicted_funding=0.00029,
        binance_predicted_funding=0.00025,
        bybit_predicted_funding=0.00027,
        atr=80,
        atr_pct=0.025,
        ma_fast=3_180,
        ma_slow=3_240,
        timestamp_ms=1,
        flow_imbalance=0.38,
        trade_stream_fresh=True,
    )

    signal = generate_signal(features)

    assert signal is not None
    assert signal.side == "short"
    assert signal.strategy == StrategyType.MEAN_REVERSION


def test_rejects_high_spread() -> None:
    features = MarketFeatures(
        symbol="BTC",
        mid_price=100_000,
        spread_bps=20,
        volume_24h=2_000_000_000,
        liquidity_score=0.95,
        current_funding_1h=0.0001,
        predicted_funding=0.0005,
        funding_persistence=5,
        funding_momentum=0.0002,
        microstructure_momentum=0.00015,
        open_interest=1_000_000,
        oi_zscore=1.4,
        oi_delta=0.5,
        cvd=15_000_000,
        cvd_delta=4_000_000,
        long_short_ratio=0.72,
        hl_predicted_funding=0.0005,
        binance_predicted_funding=0.00045,
        bybit_predicted_funding=0.0004,
        atr=1_000,
        atr_pct=0.01,
        ma_fast=100_500,
        ma_slow=99_700,
        timestamp_ms=1,
        flow_imbalance=0.62,
        trade_stream_fresh=True,
    )

    assert generate_signal(features) is None
