from trading_system.signals.engine import generate_signal
from trading_system.signals.models import MarketFeatures, StrategyType


def test_generates_continuation_long_signal() -> None:
    features = MarketFeatures(
        symbol="BTC",
        mid_price=100_000,
        spread_bps=1,
        current_funding_1h=0.0001,
        predicted_funding=0.0005,
        funding_persistence=5,
        funding_momentum=0.0002,
        open_interest=1_000_000,
        oi_delta=0.5,
        cvd=1_000,
        cvd_delta=2_000,
        long_short_ratio=0.60,
        hl_predicted_funding=0.0005,
        binance_predicted_funding=0.00045,
        bybit_predicted_funding=0.0004,
        atr=1_000,
        timestamp_ms=1,
    )

    signal = generate_signal(features)

    assert signal is not None
    assert signal.side == "long"
    assert signal.strategy == StrategyType.CONTINUATION


def test_rejects_high_spread() -> None:
    features = MarketFeatures(
        symbol="BTC",
        mid_price=100_000,
        spread_bps=20,
        current_funding_1h=0.0001,
        predicted_funding=0.0005,
        funding_persistence=5,
        funding_momentum=0.0002,
        open_interest=1_000_000,
        oi_delta=0.5,
        cvd=1_000,
        cvd_delta=2_000,
        long_short_ratio=0.60,
        hl_predicted_funding=0.0005,
        binance_predicted_funding=0.00045,
        bybit_predicted_funding=0.0004,
        atr=1_000,
        timestamp_ms=1,
    )

    assert generate_signal(features) is None
