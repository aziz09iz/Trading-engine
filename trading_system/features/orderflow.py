from dataclasses import dataclass


@dataclass
class CvdState:
    value: float = 0.0


def update_cvd(state: CvdState, trade_price: float, mid_price: float, size: float) -> float:
    if trade_price >= mid_price:
        state.value += size
    else:
        state.value -= size
    return state.value


def spread_bps(bid: float, ask: float) -> float:
    mid = (bid + ask) / 2
    if mid <= 0:
        return 10_000.0
    return (ask - bid) / mid * 10_000
