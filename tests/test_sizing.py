from trading_system.risk.sizing import AccountState, SizingConfig, position_size_usd
from trading_system.signals.models import StrategyType, TradeSignal


def test_position_size_is_capped_by_exposure() -> None:
    signal = TradeSignal(
        symbol="BTC",
        side="long",
        strategy=StrategyType.CONTINUATION,
        strength=0.90,
        funding_score=0.9,
        positioning_score=0.8,
        orderflow_score=0.7,
        alignment_score=0.8,
        trend_score=0.6,
        suggested_risk_pct=0.0075,
        reason="test",
    )
    account = AccountState(
        equity_usd=10_000,
        daily_pnl_usd=0,
        total_exposure_usd=2_900,
        open_positions=1,
    )

    size = position_size_usd(signal, account, 100_000, 99_000, SizingConfig())

    assert size == 100


def test_daily_drawdown_blocks_new_positions() -> None:
    signal = TradeSignal(
        symbol="BTC",
        side="long",
        strategy=StrategyType.CONTINUATION,
        strength=0.90,
        funding_score=0.9,
        positioning_score=0.8,
        orderflow_score=0.7,
        alignment_score=0.8,
        trend_score=0.6,
        suggested_risk_pct=0.0075,
        reason="test",
    )
    account = AccountState(
        equity_usd=10_000,
        daily_pnl_usd=-301,
        total_exposure_usd=0,
        open_positions=0,
    )

    size = position_size_usd(signal, account, 100_000, 99_000, SizingConfig())

    assert size == 0
