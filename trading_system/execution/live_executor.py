from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from time import time
from uuid import uuid4

from trading_system.app.user_settings import HyperliquidCredentials, TradingParameters
from trading_system.execution.hyperliquid_client import HyperliquidExecutionClient, OrderRequest, build_exchange_client
from trading_system.signals.models import MarketFeatures, TradeSignal


def round_size(size: float, decimals: int) -> float:
    quant = Decimal("1").scaleb(-max(decimals, 0))
    return float(Decimal(str(size)).quantize(quant, rounding=ROUND_DOWN))


def format_price(price: float, size_decimals: int) -> float:
    if price <= 0:
        return 0.0
    decimal_price = Decimal(str(price))
    max_decimals = max(0, 6 - max(size_decimals, 0))
    sig_decimal_places = max(0, 4 - decimal_price.adjusted())
    allowed_decimals = min(max_decimals, sig_decimal_places)
    quant = Decimal("1").scaleb(-allowed_decimals)
    return float(decimal_price.quantize(quant, rounding=ROUND_DOWN))


@dataclass
class ExecutionResult:
    symbol: str
    status: str
    message: str
    response: dict[str, object] | None = None


class LiveExecutionService:
    def __init__(self) -> None:
        self._last_submitted_at: dict[str, float] = {}

    def can_submit(self, symbol: str, cooldown_seconds: int) -> bool:
        last = self._last_submitted_at.get(symbol, 0.0)
        return (time() - last) >= cooldown_seconds

    async def submit_order(
        self,
        signal: TradeSignal,
        market: MarketFeatures,
        notional_usd: float,
        credentials: HyperliquidCredentials,
        trading: TradingParameters,
    ) -> ExecutionResult:
        if trading.shadow_mode:
            return ExecutionResult(symbol=signal.symbol, status="shadow", message="shadow mode enabled")
        if not credentials.account_address or not credentials.secret_key:
            return ExecutionResult(symbol=signal.symbol, status="blocked", message="missing Hyperliquid credentials")
        if not self.can_submit(signal.symbol, trading.execution_cooldown_seconds):
            return ExecutionResult(symbol=signal.symbol, status="cooldown", message="submission cooldown active")

        exchange = build_exchange_client(credentials)
        if exchange is None:
            return ExecutionResult(symbol=signal.symbol, status="blocked", message="SDK not available")

        client = HyperliquidExecutionClient(exchange)
        side = "buy" if signal.side == "long" else "sell"
        limit_price = format_price(market.mid_price, market.size_decimals)
        size = round_size(notional_usd / max(limit_price, 1e-9), market.size_decimals)
        if size <= 0:
            return ExecutionResult(symbol=signal.symbol, status="blocked", message="computed order size is zero")

        request = OrderRequest(
            symbol=signal.symbol,
            side=side,
            size=size,
            price=limit_price,
            reduce_only=trading.reduce_only_mode,
            tif="Alo",
            cloid=f"0x{uuid4().hex}",
        )
        response = await client.place_limit(request)
        self._last_submitted_at[signal.symbol] = time()
        return ExecutionResult(
            symbol=signal.symbol,
            status="submitted",
            message="order submitted to Hyperliquid",
            response=response if isinstance(response, dict) else {"raw": response},
        )
