from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import time

import httpx


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class LivePosition:
    symbol: str
    side: str
    size: float
    notional_usd: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    leverage: float
    margin_mode: str
    liquidation_price: float | None


@dataclass(frozen=True)
class LiveOrder:
    symbol: str
    side: str
    size: float
    remaining_size: float
    limit_price: float
    reduce_only: bool
    order_type: str
    status: str
    oid: int
    timestamp_ms: int


@dataclass(frozen=True)
class LiveFill:
    symbol: str
    side: str
    size: float
    price: float
    fee: float
    closed_pnl: float
    direction: str
    crossed: bool
    timestamp_ms: int


@dataclass(frozen=True)
class AccountSnapshot:
    account_value: float
    withdrawable: float
    total_notional: float
    total_margin_used: float
    cross_maintenance_margin_used: float
    positions: list[LivePosition]
    open_orders: list[LiveOrder]
    fills: list[LiveFill]


class HyperliquidAccountClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def _post_info(self, client: httpx.AsyncClient, payload: dict[str, object]) -> object:
        response = await client.post(f"{self.base_url}/info", json=payload)
        response.raise_for_status()
        return response.json()

    async def fetch_snapshot(self, user: str) -> AccountSnapshot:
        if not user:
            return AccountSnapshot(0.0, 0.0, 0.0, 0.0, 0.0, [], [], [])

        async with httpx.AsyncClient(timeout=15.0) as client:
            now_ms = int(time() * 1000)
            state_payload, orders_payload, fills_payload = await asyncio.gather(
                self._post_info(client, {"type": "clearinghouseState", "user": user}),
                self._post_info(client, {"type": "frontendOpenOrders", "user": user}),
                self._post_info(
                    client,
                    {
                        "type": "userFillsByTime",
                        "user": user,
                        "startTime": now_ms - (24 * 60 * 60 * 1000),
                        "endTime": now_ms,
                        "aggregateByTime": True,
                    },
                ),
            )

        return AccountSnapshot(
            account_value=_to_float(state_payload.get("marginSummary", {}).get("accountValue")) if isinstance(state_payload, dict) else 0.0,
            withdrawable=_to_float(state_payload.get("withdrawable")) if isinstance(state_payload, dict) else 0.0,
            total_notional=_to_float(state_payload.get("marginSummary", {}).get("totalNtlPos")) if isinstance(state_payload, dict) else 0.0,
            total_margin_used=_to_float(state_payload.get("marginSummary", {}).get("totalMarginUsed")) if isinstance(state_payload, dict) else 0.0,
            cross_maintenance_margin_used=_to_float(state_payload.get("crossMaintenanceMarginUsed")) if isinstance(state_payload, dict) else 0.0,
            positions=self._parse_positions(state_payload),
            open_orders=self._parse_orders(orders_payload),
            fills=self._parse_fills(fills_payload),
        )

    def _parse_positions(self, payload: object) -> list[LivePosition]:
        if not isinstance(payload, dict):
            return []
        rows: list[LivePosition] = []
        for item in payload.get("assetPositions", []):
            if not isinstance(item, dict):
                continue
            position = item.get("position", {})
            if not isinstance(position, dict):
                continue
            size = abs(_to_float(position.get("szi")))
            entry_price = _to_float(position.get("entryPx"))
            mark_price = _to_float(position.get("markPx"))
            side = "long" if _to_float(position.get("szi")) >= 0 else "short"
            rows.append(
                LivePosition(
                    symbol=str(position.get("coin") or ""),
                    side=side,
                    size=size,
                    notional_usd=abs(_to_float(position.get("positionValue"))),
                    entry_price=entry_price,
                    mark_price=mark_price,
                    unrealized_pnl=_to_float(position.get("unrealizedPnl")),
                    leverage=_to_float(position.get("leverage", {}).get("value") if isinstance(position.get("leverage"), dict) else position.get("leverage")),
                    margin_mode=str(position.get("leverage", {}).get("type") if isinstance(position.get("leverage"), dict) else "cross"),
                    liquidation_price=_to_float(position.get("liquidationPx")) or None,
                )
            )
        return rows

    def _parse_orders(self, payload: object) -> list[LiveOrder]:
        if not isinstance(payload, list):
            return []
        rows: list[LiveOrder] = []
        for order in payload:
            if not isinstance(order, dict):
                continue
            rows.append(
                LiveOrder(
                    symbol=str(order.get("coin") or ""),
                    side="buy" if str(order.get("side") or "").upper().startswith("B") else "sell",
                    size=_to_float(order.get("origSz")),
                    remaining_size=_to_float(order.get("sz")),
                    limit_price=_to_float(order.get("limitPx")),
                    reduce_only=bool(order.get("reduceOnly")),
                    order_type=str(order.get("orderType") or "Limit"),
                    status="open",
                    oid=int(_to_float(order.get("oid"))),
                    timestamp_ms=int(_to_float(order.get("timestamp"))),
                )
            )
        return rows

    def _parse_fills(self, payload: object) -> list[LiveFill]:
        if not isinstance(payload, list):
            return []
        rows: list[LiveFill] = []
        for fill in payload[:50]:
            if not isinstance(fill, dict):
                continue
            rows.append(
                LiveFill(
                    symbol=str(fill.get("coin") or ""),
                    side="buy" if str(fill.get("side") or "").upper().startswith("B") else "sell",
                    size=_to_float(fill.get("sz")),
                    price=_to_float(fill.get("px")),
                    fee=_to_float(fill.get("fee")),
                    closed_pnl=_to_float(fill.get("closedPnl")),
                    direction=str(fill.get("dir") or ""),
                    crossed=bool(fill.get("crossed")),
                    timestamp_ms=int(_to_float(fill.get("time"))),
                )
            )
        return rows

