from __future__ import annotations

import asyncio
import json

import websockets

from trading_system.features.orderflow import TradeFlowStore


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class HyperliquidTradeStream:
    def __init__(self, flow_store: TradeFlowStore) -> None:
        self.flow_store = flow_store
        self._symbols: set[str] = set()
        self._ws_url: str = ""
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._resubscribe_event = asyncio.Event()

    async def start(self, ws_url: str, symbols: list[str]) -> None:
        next_symbols = set(symbols)
        if not next_symbols:
            return

        url_changed = bool(self._ws_url and self._ws_url != ws_url)
        self._ws_url = ws_url
        if self._task is None or self._task.done():
            self._stop_event = asyncio.Event()
            self._resubscribe_event = asyncio.Event()
            self._symbols = next_symbols
            self._task = asyncio.create_task(self._run())
            return

        if url_changed:
            await self.stop()
            self._symbols = next_symbols
            self._stop_event = asyncio.Event()
            self._resubscribe_event = asyncio.Event()
            self._task = asyncio.create_task(self._run())
            return

        if next_symbols != self._symbols:
            self._symbols = next_symbols
            self._resubscribe_event.set()

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self._consume()
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(2.0)

    async def _consume(self) -> None:
        async with websockets.connect(self._ws_url, ping_interval=20, ping_timeout=20) as ws:
            await self._subscribe(ws)
            while not self._stop_event.is_set():
                if self._resubscribe_event.is_set():
                    self._resubscribe_event.clear()
                    await self._subscribe(ws)
                message = await asyncio.wait_for(ws.recv(), timeout=45)
                await self._handle_message(message)

    async def _subscribe(self, ws) -> None:
        for symbol in sorted(self._symbols):
            await ws.send(
                json.dumps(
                    {
                        "method": "subscribe",
                        "subscription": {
                            "type": "trades",
                            "coin": symbol,
                        },
                    }
                )
            )

    async def _handle_message(self, raw: str) -> None:
        payload = json.loads(raw)
        if payload.get("channel") != "trades":
            return
        trades = payload.get("data", [])
        if not isinstance(trades, list):
            return
        for trade in trades:
            if not isinstance(trade, dict):
                continue
            symbol = str(trade.get("coin") or "")
            if not symbol:
                continue
            self.flow_store.record_trade(
                symbol=symbol,
                side=str(trade.get("side") or ""),
                price=_to_float(trade.get("px")),
                size=_to_float(trade.get("sz")),
                timestamp_ms=int(_to_float(trade.get("time"))),
            )
