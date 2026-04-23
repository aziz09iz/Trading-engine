from dataclasses import dataclass
from typing import Literal

Side = Literal["long", "short"]


@dataclass(frozen=True)
class BookTop:
    bid: float
    ask: float
    bid_size: float
    ask_size: float


@dataclass(frozen=True)
class ExecutionPlan:
    side: Side
    limit_price: float
    size_usd: float
    post_only: bool
    reduce_only: bool = False


def make_adaptive_entry(
    side: Side,
    book: BookTop,
    size_usd: float,
    max_spread_bps: float = 5.0,
    join_bps: float = 0.5,
) -> ExecutionPlan | None:
    mid = (book.bid + book.ask) / 2
    if mid <= 0:
        return None

    spread_bps = (book.ask - book.bid) / mid * 10_000
    if spread_bps > max_spread_bps:
        return None

    offset = mid * join_bps / 10_000
    price = min(book.bid + offset, book.ask) if side == "long" else max(book.ask - offset, book.bid)

    return ExecutionPlan(
        side=side,
        limit_price=round(price, 6),
        size_usd=size_usd,
        post_only=True,
    )
