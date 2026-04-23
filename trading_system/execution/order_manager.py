import asyncio

from trading_system.execution.adaptive_limit import BookTop, make_adaptive_entry
from trading_system.execution.hyperliquid_client import HyperliquidExecutionClient, OrderRequest
from trading_system.signals.models import TradeSignal


class OrderManager:
    def __init__(self, client: HyperliquidExecutionClient):
        self.client = client

    async def enter(self, signal: TradeSignal, book: BookTop, notional_usd: float) -> dict | None:
        plan = make_adaptive_entry(signal.side, book, notional_usd)
        if plan is None:
            return None

        base_size = notional_usd / plan.limit_price
        side = "buy" if signal.side == "long" else "sell"
        request = OrderRequest(
            symbol=signal.symbol,
            side=side,
            size=base_size,
            price=plan.limit_price,
            reduce_only=False,
            tif="Alo",
        )
        result = await self.client.place_limit(request)
        await asyncio.sleep(1.0)
        return result
