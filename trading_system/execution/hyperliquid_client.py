import asyncio
from dataclasses import dataclass
from typing import Literal, Protocol

from trading_system.app.user_settings import HyperliquidCredentials
from trading_system.data.networks import apply_network_defaults


class HyperliquidExchangeLike(Protocol):
    def order(self, name: str, is_buy: bool, sz: float, limit_px: float, order_type: dict) -> dict:
        ...

    def cancel(self, name: str, oid: int) -> dict:
        ...

    def market_close(self, coin: str) -> dict:
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
        return await asyncio.to_thread(
            self.exchange.order,
            request.symbol,
            is_buy,
            request.size,
            request.price,
            {"limit": {"tif": request.tif}},
            request.reduce_only,
            request.cloid,
        )

    async def cancel(self, symbol: str, oid: int) -> dict:
        return await asyncio.to_thread(self.exchange.cancel, symbol, oid)


def build_exchange_client(credentials: HyperliquidCredentials) -> HyperliquidExchangeLike | None:
    try:
        from eth_account import Account
        from hyperliquid.exchange import Exchange
    except ImportError:
        return None

    resolved = apply_network_defaults(credentials)
    wallet = Account.from_key(resolved.secret_key)
    return Exchange(wallet, resolved.api_url, account_address=resolved.account_address or None)
