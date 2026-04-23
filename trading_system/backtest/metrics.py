import math


def max_drawdown(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0

    peak = equity_curve[0]
    max_dd = 0.0
    for equity in equity_curve:
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak)
    return max_dd


def sharpe_ratio(returns: list[float], periods_per_year: int = 365 * 24) -> float:
    if len(returns) < 2:
        return 0.0

    avg = sum(returns) / len(returns)
    variance = sum((ret - avg) ** 2 for ret in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    if std == 0:
        return 0.0
    return avg / std * math.sqrt(periods_per_year)


def win_rate(pnls: list[float]) -> float:
    if not pnls:
        return 0.0
    return sum(1 for pnl in pnls if pnl > 0) / len(pnls)


def expectancy(pnls: list[float]) -> float:
    if not pnls:
        return 0.0
    return sum(pnls) / len(pnls)
