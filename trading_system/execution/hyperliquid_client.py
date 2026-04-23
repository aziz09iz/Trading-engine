import asyncio
from dataclasses import dataclass
from typing import Literal, Protocol


class HyperliquidExchangeLike(Protocol):
    def order(self, name: str, is_buy: bool, sz: float, limit_px: float, order_type: dict) -> dict:
        ...

    def cancel(self, name: str, oid: int) -> dict:
        ...


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: Literal["buy", "sell"]
    size: float
    price: float
    reduce_only: bool = False
    tif: Literal["Alo", "Ioc", "Gtc"] = "Alo"
    cloid: str | None = None


class HyperliquidExecutionClient:
    def __init__(self, exchange_client: HyperliquidExchangeLike):
        self.exchange = exchange_client

    async def place_limit(self, request: OrderRequest) -> dict:
        is_buy = request.side == "buy"
        order_type = {
            "limit": {"tif": request.tif},
            "reduceOnly": request.reduce_only,
        }
        return await asyncio.to_thread(
            self.exchange.order,
            request.symbol,
            is_buy,
            request.size,
            request.price,
            order_type,
        )

    async def cancel(self, symbol: str, oid: int) -> dict:
        return await asyncio.to_thread(self.exchange.cancel, symbol, oid)
