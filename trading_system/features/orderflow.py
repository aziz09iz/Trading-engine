from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class SymbolFlowState:
    cvd: float = 0.0
    recent_signed_notional: deque[float] = field(default_factory=lambda: deque(maxlen=64))
    last_trade_ts: int = 0
    buy_volume: float = 0.0
    sell_volume: float = 0.0


class TradeFlowStore:
    def __init__(self, max_recent: int = 64) -> None:
        self.max_recent = max_recent
        self._state: dict[str, SymbolFlowState] = {}

    def state_for(self, symbol: str) -> SymbolFlowState:
        state = self._state.get(symbol)
        if state is None:
            state = SymbolFlowState(recent_signed_notional=deque(maxlen=self.max_recent))
            self._state[symbol] = state
        return state

    def record_trade(
        self,
        symbol: str,
        side: str,
        price: float,
        size: float,
        timestamp_ms: int,
    ) -> None:
        state = self.state_for(symbol)
        notional = price * size
        side_upper = side.upper()
        signed = notional if side_upper.startswith("B") else -notional
        state.cvd += signed
        state.recent_signed_notional.append(signed)
        state.last_trade_ts = timestamp_ms
        if signed >= 0:
            state.buy_volume += notional
        else:
            state.sell_volume += abs(notional)

    def cvd(self, symbol: str) -> float:
        return self.state_for(symbol).cvd

    def cvd_delta(self, symbol: str) -> float:
        state = self.state_for(symbol)
        return sum(state.recent_signed_notional)

    def imbalance_ratio(self, symbol: str) -> float:
        state = self.state_for(symbol)
        total = state.buy_volume + state.sell_volume
        if total <= 0:
            return 0.5
        return state.buy_volume / total

    def last_trade_age_ms(self, symbol: str, now_ms: int) -> int | None:
        state = self._state.get(symbol)
        if state is None or state.last_trade_ts <= 0:
            return None
        return max(now_ms - state.last_trade_ts, 0)


def spread_bps(bid: float, ask: float) -> float:
    mid = (bid + ask) / 2
    if mid <= 0:
        return 10_000.0
    return (ask - bid) / mid * 10_000
