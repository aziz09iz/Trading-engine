from dataclasses import dataclass

from trading_system.signals.models import TradeSignal


@dataclass(frozen=True)
class AccountState:
    equity_usd: float
    daily_pnl_usd: float
    total_exposure_usd: float
    open_positions: int


@dataclass(frozen=True)
class SizingConfig:
    min_risk_pct: float = 0.0025
    max_risk_pct: float = 0.0075
    max_total_exposure_pct: float = 0.30
    max_positions: int = 6
    daily_drawdown_stop_pct: float = 0.03


def risk_pct_for_signal(signal: TradeSignal, config: SizingConfig) -> float:
    if signal.suggested_risk_pct > 0:
        return max(config.min_risk_pct, min(config.max_risk_pct, signal.suggested_risk_pct))

    if signal.strength <= 0.70:
        return config.min_risk_pct

    scaled = config.min_risk_pct + ((signal.strength - 0.70) / 0.15) * (
        config.max_risk_pct - config.min_risk_pct
    )
    return max(config.min_risk_pct, min(config.max_risk_pct, scaled))


def position_size_usd(
    signal: TradeSignal,
    account: AccountState,
    entry_price: float,
    stop_price: float,
    config: SizingConfig,
) -> float:
    if account.open_positions >= config.max_positions:
        return 0.0

    if account.daily_pnl_usd <= -account.equity_usd * config.daily_drawdown_stop_pct:
        return 0.0

    max_exposure = account.equity_usd * config.max_total_exposure_pct
    remaining_exposure = max(0.0, max_exposure - account.total_exposure_usd)
    if remaining_exposure <= 0:
        return 0.0

    stop_distance = abs(entry_price - stop_price)
    if stop_distance <= 0:
        return 0.0

    risk_usd = account.equity_usd * risk_pct_for_signal(signal, config)
    size_base = risk_usd / stop_distance
    return min(size_base * entry_price, remaining_exposure)
