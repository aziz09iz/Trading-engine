from dataclasses import dataclass


@dataclass(frozen=True)
class Fill:
    symbol: str
    side: str
    price: float
    size: float
    fee: float
    timestamp_ms: int


class SimBroker:
    def __init__(self, equity: float, taker_fee_bps: float = 4.0, maker_fee_bps: float = 1.5):
        self.equity = equity
        self.taker_fee_bps = taker_fee_bps
        self.maker_fee_bps = maker_fee_bps
        self.fills: list[Fill] = []

    def execute_limit(
        self,
        symbol: str,
        side: str,
        limit_price: float,
        size: float,
        bid: float,
        ask: float,
        timestamp_ms: int,
        post_only: bool = True,
    ) -> Fill | None:
        if post_only:
            return None

        if side == "buy" and limit_price >= ask:
            fill_price = ask
        elif side == "sell" and limit_price <= bid:
            fill_price = bid
        else:
            return None

        fee = fill_price * size * self.taker_fee_bps / 10_000
        self.equity -= fee
        fill = Fill(symbol, side, fill_price, size, fee, timestamp_ms)
        self.fills.append(fill)
        return fill
