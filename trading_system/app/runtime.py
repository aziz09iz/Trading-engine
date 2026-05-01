from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from time import time

from trading_system.app.config import settings
from trading_system.app.user_settings import SettingsStore, UserSettings, UserSettingsUpdate
from trading_system.data.account_state import AccountSnapshot, HyperliquidAccountClient
from trading_system.data.hyperliquid_info import HyperliquidInfoClient
from trading_system.data.networks import apply_network_defaults
from trading_system.data.trade_stream import HyperliquidTradeStream
from trading_system.execution.live_executor import ExecutionResult, LiveExecutionService
from trading_system.features.oi_history import OpenInterestHistory
from trading_system.features.orderflow import TradeFlowStore
from trading_system.notifications.telegram import TelegramNotifier
from trading_system.risk.sizing import AccountState, SizingConfig, position_size_usd, risk_pct_for_signal
from trading_system.signals.engine import rank_trade_candidates
from trading_system.signals.models import TradeSignal


@dataclass
class EngineSnapshot:
    last_error: str | None = None
    generated_at: float | None = None
    migration_ok: bool = False
    migration_error: str | None = None
    universe: list[dict[str, object]] = field(default_factory=list)
    signals: list[dict[str, object]] = field(default_factory=list)
    orders: list[dict[str, object]] = field(default_factory=list)
    metrics: dict[str, object] = field(default_factory=dict)
    positions: list[dict[str, object]] = field(default_factory=list)
    open_orders: list[dict[str, object]] = field(default_factory=list)
    fills: list[dict[str, object]] = field(default_factory=list)
    activity: list[str] = field(default_factory=list)


class TradingRuntime:
    def __init__(self) -> None:
        self.settings_store = SettingsStore(settings.runtime_settings_path)
        self.flow_store = TradeFlowStore()
        self.client = HyperliquidInfoClient(self.user_settings.hyperliquid.api_url, flow_store=self.flow_store)
        self.account_client = HyperliquidAccountClient(self.user_settings.hyperliquid.api_url)
        self.trade_stream = HyperliquidTradeStream(self.flow_store)
        self.oi_history = OpenInterestHistory(
            path=settings.runtime_state_path,
            window=settings.oi_history_window,
        )
        self.account = AccountState(
            equity_usd=100_000.0,
            daily_pnl_usd=0.0,
            total_exposure_usd=0.0,
            open_positions=0,
        )
        self.snapshot = EngineSnapshot()
        self.execution = LiveExecutionService()
        self.telegram = TelegramNotifier()
        self._task: asyncio.Task | None = None
        self._last_summary_sent_at = 0.0
        self._last_runtime_error = ""
        self._last_runtime_ok = False
        self._recent_activity: list[str] = []

    @property
    def user_settings(self) -> UserSettings:
        return self.settings_store.settings

    def _reset_clients(self) -> None:
        credentials = apply_network_defaults(self.user_settings.hyperliquid)
        self.client = HyperliquidInfoClient(credentials.api_url, flow_store=self.flow_store)
        self.account_client = HyperliquidAccountClient(credentials.api_url)

    def update_settings(self, update: UserSettingsUpdate) -> UserSettings:
        updated = self.settings_store.update(update)
        self._reset_clients()
        return updated

    def set_migration_status(self, ok: bool, error: str | None = None) -> None:
        self.snapshot.migration_ok = ok
        self.snapshot.migration_error = error

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self.trade_stream.stop()

    async def _run(self) -> None:
        while True:
            try:
                await self.refresh()
            except Exception as exc:  # pragma: no cover
                self.snapshot.last_error = str(exc)
                await self._notify_error(str(exc))
            await asyncio.sleep(self.user_settings.trading.refresh_seconds)

    async def refresh(self) -> EngineSnapshot:
        credentials = apply_network_defaults(self.user_settings.hyperliquid)
        live = await self.client.fetch_market_snapshot(
            self.oi_history,
            top_n=self.user_settings.trading.top_n_markets,
            include_external_sentiment=self.user_settings.trading.use_external_sentiment,
            use_trade_stream=self.user_settings.trading.use_real_trade_stream,
        )
        if self.user_settings.trading.use_real_trade_stream:
            await self.trade_stream.start(credentials.ws_url, [market.symbol for market in live.universe])
        eligible_markets = [
            market
            for market in live.markets
            if market.spread_bps <= self.user_settings.trading.max_spread_bps
            and market.liquidity_score >= self.user_settings.trading.min_liquidity_score
        ]
        market_map = {row.symbol: row for row in eligible_markets}
        ranked = [
            signal
            for signal in rank_trade_candidates(eligible_markets)
            if signal.strength >= self.user_settings.trading.min_signal_strength
            and (
                not self.user_settings.trading.require_trend_alignment
                or abs(signal.trend_score) >= 0.05
            )
            and (
                not self.user_settings.trading.require_cross_exchange_alignment
                or abs(signal.alignment_score) >= 0.05
            )
        ]

        account_snapshot = await self.account_client.fetch_snapshot(credentials.account_address)
        self._sync_account_from_snapshot(account_snapshot)

        orders = [self._make_order(signal, market_map=market_map) for signal in ranked[: self.user_settings.trading.max_concurrent_positions]]
        executed_orders = await self._execute_orders([order for order in orders if order], ranked, market_map)

        self.snapshot = EngineSnapshot(
            last_error=None,
            generated_at=time(),
            migration_ok=self.snapshot.migration_ok,
            migration_error=self.snapshot.migration_error,
            universe=[
                {
                    "symbol": market.symbol,
                    "volume_24h": market.volume_24h,
                    "spread_bps": market.spread_bps,
                    "open_interest_usd": market.open_interest_usd,
                }
                for market in live.universe
            ],
            signals=[self._signal_payload(signal, market_map) for signal in ranked],
            orders=executed_orders,
            metrics=self._metrics_payload(ranked, eligible_markets, account_snapshot),
            positions=[self._position_payload(row) for row in account_snapshot.positions],
            open_orders=[self._open_order_payload(row) for row in account_snapshot.open_orders],
            fills=[self._fill_payload(row) for row in account_snapshot.fills],
            activity=self._recent_activity[-12:],
        )
        await self._maybe_notify_runtime(ranked, executed_orders, account_snapshot)
        return self.snapshot

    def _sync_account_from_snapshot(self, snapshot: AccountSnapshot) -> None:
        equity = snapshot.account_value or self.account.equity_usd
        total_exposure = sum(abs(position.notional_usd) for position in snapshot.positions)
        daily_pnl = sum(fill.closed_pnl for fill in snapshot.fills if fill.closed_pnl)
        self.account = AccountState(
            equity_usd=equity,
            daily_pnl_usd=daily_pnl,
            total_exposure_usd=total_exposure,
            open_positions=len(snapshot.positions),
        )

    def _signal_payload(self, signal: TradeSignal, market_map: dict[str, object]) -> dict[str, object]:
        market = market_map[signal.symbol]
        return {
            "symbol": signal.symbol,
            "side": signal.side,
            "strategy": signal.strategy.value,
            "strength": signal.strength,
            "funding": market.current_funding_1h,
            "predicted_funding": market.predicted_funding,
            "oi_delta": market.oi_delta,
            "oi_zscore": market.oi_zscore,
            "cvd": market.cvd,
            "cvd_delta": market.cvd_delta,
            "long_short_ratio": market.long_short_ratio,
            "alignment": signal.alignment_score,
            "risk_pct": signal.suggested_risk_pct,
            "reason": signal.reason,
            "tp1": signal.take_profit_prices[0] if signal.take_profit_prices else None,
            "tp2": signal.take_profit_prices[1] if signal.take_profit_prices else None,
            "stop": signal.invalidation_price,
            "flow_imbalance": market.flow_imbalance,
            "trade_stream_fresh": market.trade_stream_fresh,
        }

    def _make_order(self, signal: TradeSignal, market_map: dict[str, object]) -> dict[str, object] | None:
        market = market_map.get(signal.symbol)
        if market is None or signal.invalidation_price is None:
            return None
        config = SizingConfig(
            min_risk_pct=self.user_settings.trading.min_risk_pct,
            max_risk_pct=self.user_settings.trading.max_risk_pct,
            max_total_exposure_pct=self.user_settings.trading.max_total_exposure_pct,
            max_positions=self.user_settings.trading.max_concurrent_positions,
            daily_drawdown_stop_pct=self.user_settings.trading.daily_drawdown_stop_pct,
        )
        notional = position_size_usd(
            signal=signal,
            account=self.account,
            entry_price=market.mid_price,
            stop_price=signal.invalidation_price,
            config=config,
        )
        if notional <= 0:
            return None
        execution_mode = "shadow" if self.user_settings.trading.shadow_mode else "live"
        return {
            "symbol": signal.symbol,
            "side": "Buy" if signal.side == "long" else "Sell",
            "type": f"{signal.strategy.value} limit",
            "price": market.mid_price,
            "notional_usd": notional,
            "risk_pct": risk_pct_for_signal(signal, config),
            "shadow_mode": self.user_settings.trading.shadow_mode,
            "reduce_only": self.user_settings.trading.reduce_only_mode,
            "status": execution_mode,
            "quality": "aggressive" if signal.strength >= self.user_settings.trading.aggressive_signal_strength else "standard",
        }

    async def _execute_orders(
        self,
        orders: list[dict[str, object]],
        ranked_signals: list[TradeSignal],
        market_map: dict[str, object],
    ) -> list[dict[str, object]]:
        signal_map = {signal.symbol: signal for signal in ranked_signals}
        executed: list[dict[str, object]] = []
        for order in orders:
            symbol = str(order["symbol"])
            signal = signal_map.get(symbol)
            market = market_map.get(symbol)
            if signal is None or market is None:
                continue
            result: ExecutionResult = await self.execution.submit_order(
                signal=signal,
                market=market,
                notional_usd=float(order["notional_usd"]),
                credentials=self.user_settings.hyperliquid,
                trading=self.user_settings.trading,
            )
            order["status"] = result.status
            order["message"] = result.message
            if result.response:
                order["exchange_response"] = result.response
            self._record_activity(f"{symbol}: {result.status} - {result.message}")
            executed.append(order)
        return executed

    async def cancel_all_orders(self) -> dict[str, object]:
        snapshot = await self.account_client.fetch_snapshot(self.user_settings.hyperliquid.account_address)
        result = await self.execution.cancel_all(self.user_settings.hyperliquid, snapshot.open_orders)
        self._record_activity(f"Cancel all requested: {result.message}")
        await self.notify_engine_action("cancel all")
        return {"status": result.status, "message": result.message, "response": result.response}

    async def flatten_all_positions(self) -> dict[str, object]:
        snapshot = await self.account_client.fetch_snapshot(self.user_settings.hyperliquid.account_address)
        result = await self.execution.flatten_all(self.user_settings.hyperliquid, snapshot.positions)
        self._record_activity(f"Flatten all requested: {result.message}")
        await self.notify_engine_action("flatten all")
        return {"status": result.status, "message": result.message, "response": result.response}

    def _metrics_payload(
        self,
        ranked: list[TradeSignal],
        markets: list[object],
        account_snapshot: AccountSnapshot,
    ) -> dict[str, object]:
        exposure = sum(
            order["notional_usd"]
            for order in [self._make_order(signal, {row.symbol: row for row in markets}) for signal in ranked[:6]]
            if order
        )
        return {
            "equity_usd": self.account.equity_usd,
            "withdrawable_usd": account_snapshot.withdrawable,
            "daily_pnl_usd": self.account.daily_pnl_usd,
            "open_risk_pct": round(sum(signal.suggested_risk_pct for signal in ranked[:2]), 4),
            "max_exposure_pct": self.user_settings.trading.max_total_exposure_pct,
            "current_exposure_pct": round(self.account.total_exposure_usd / self.account.equity_usd, 4)
            if self.account.equity_usd
            else 0.0,
            "queued_exposure_pct": round(exposure / self.account.equity_usd, 4) if self.account.equity_usd else 0.0,
            "signals_count": len(ranked),
            "tracked_markets": len(markets),
            "max_concurrent_positions": self.user_settings.trading.max_concurrent_positions,
            "daily_drawdown_stop_pct": self.user_settings.trading.daily_drawdown_stop_pct,
            "shadow_mode": self.user_settings.trading.shadow_mode,
            "reduce_only_mode": self.user_settings.trading.reduce_only_mode,
            "execution_cooldown_seconds": self.user_settings.trading.execution_cooldown_seconds,
            "network": apply_network_defaults(self.user_settings.hyperliquid).network,
            "positions_count": len(account_snapshot.positions),
            "open_orders_count": len(account_snapshot.open_orders),
            "fills_count": len(account_snapshot.fills),
        }

    def _position_payload(self, row) -> dict[str, object]:
        return {
            "symbol": row.symbol,
            "side": row.side,
            "size": row.size,
            "notional_usd": row.notional_usd,
            "entry_price": row.entry_price,
            "mark_price": row.mark_price,
            "unrealized_pnl": row.unrealized_pnl,
            "leverage": row.leverage,
            "margin_mode": row.margin_mode,
            "liquidation_price": row.liquidation_price,
        }

    def _open_order_payload(self, row) -> dict[str, object]:
        return {
            "symbol": row.symbol,
            "side": row.side,
            "size": row.size,
            "remaining_size": row.remaining_size,
            "limit_price": row.limit_price,
            "reduce_only": row.reduce_only,
            "order_type": row.order_type,
            "status": row.status,
            "oid": row.oid,
            "timestamp_ms": row.timestamp_ms,
        }

    def _fill_payload(self, row) -> dict[str, object]:
        return {
            "symbol": row.symbol,
            "side": row.side,
            "size": row.size,
            "price": row.price,
            "fee": row.fee,
            "closed_pnl": row.closed_pnl,
            "direction": row.direction,
            "crossed": row.crossed,
            "timestamp_ms": row.timestamp_ms,
        }

    def _record_activity(self, message: str) -> None:
        timestamp = time()
        self._recent_activity.append(f"{int(timestamp)} {message}")
        self._recent_activity = self._recent_activity[-50:]

    async def notify_engine_action(self, action: str) -> None:
        telegram = self.user_settings.telegram
        if not (telegram.notify_engine_actions and self.telegram.enabled(telegram)):
            return
        mode = "shadow" if self.user_settings.trading.shadow_mode else "live"
        await self._safe_send_telegram(
            telegram,
            f"Engine action: {action}\nMode: {mode}\nNetwork: {apply_network_defaults(self.user_settings.hyperliquid).network}",
        )

    async def send_telegram_test(self) -> bool:
        telegram = self.user_settings.telegram
        try:
            return await self.telegram.send_message(
                telegram,
                "Trading engine Telegram test message.\nNotifications and bot configuration are valid.",
            )
        except Exception:  # pragma: no cover
            return False

    async def _maybe_notify_runtime(
        self,
        ranked: list[TradeSignal],
        executed_orders: list[dict[str, object]],
        account_snapshot: AccountSnapshot,
    ) -> None:
        telegram = self.user_settings.telegram
        if not self.telegram.enabled(telegram):
            return

        if self.snapshot.last_error:
            if telegram.notify_errors and self.snapshot.last_error != self._last_runtime_error:
                await self._safe_send_telegram(telegram, f"Runtime error detected:\n{self.snapshot.last_error}")
            self._last_runtime_error = self.snapshot.last_error
            self._last_runtime_ok = False
            return

        if telegram.notify_api_status and not self._last_runtime_ok:
            await self._safe_send_telegram(
                telegram,
                f"API status: online\nMigration: {'ok' if self.snapshot.migration_ok else 'pending'}\nMode: {'shadow' if self.user_settings.trading.shadow_mode else 'live'}",
            )
        self._last_runtime_error = ""
        self._last_runtime_ok = True

        if telegram.notify_trade_activity:
            for order in executed_orders:
                if order.get("status") in {"submitted", "blocked", "cooldown", "shadow"}:
                    await self._safe_send_telegram(
                        telegram,
                        "\n".join(
                            [
                                f"Trade activity: {order['status']}",
                                f"Symbol: {order['symbol']}",
                                f"Side: {order['side']}",
                                f"Notional: {order['notional_usd']:.2f} USD",
                                f"Message: {order.get('message', '-')}",
                            ]
                        ),
                    )

        if telegram.notify_pnl_summary:
            interval_seconds = max(telegram.summary_interval_minutes, 1) * 60
            now = time()
            if (now - self._last_summary_sent_at) >= interval_seconds:
                top_signal = ranked[0] if ranked else None
                summary_lines = [
                    "Engine summary",
                    f"Mode: {'shadow' if self.user_settings.trading.shadow_mode else 'live'}",
                    f"Network: {apply_network_defaults(self.user_settings.hyperliquid).network}",
                    f"Tracked markets: {self.snapshot.metrics.get('tracked_markets', 0)}",
                    f"Signals: {self.snapshot.metrics.get('signals_count', 0)}",
                    f"Positions: {len(account_snapshot.positions)}",
                    f"Open orders: {len(account_snapshot.open_orders)}",
                    f"Exposure: {self.snapshot.metrics.get('current_exposure_pct', 0) * 100:.2f}%",
                    f"Daily PnL: {self.snapshot.metrics.get('daily_pnl_usd', 0):.2f} USD",
                ]
                if top_signal is not None:
                    summary_lines.append(
                        f"Top signal: {top_signal.symbol} {top_signal.side} strength {top_signal.strength:.2f}"
                    )
                await self._safe_send_telegram(telegram, "\n".join(summary_lines))
                self._last_summary_sent_at = now

    async def _notify_error(self, message: str) -> None:
        telegram = self.user_settings.telegram
        if not (telegram.notify_errors and self.telegram.enabled(telegram)):
            return
        if message == self._last_runtime_error:
            return
        self._last_runtime_error = message
        self._last_runtime_ok = False
        await self._safe_send_telegram(telegram, f"Runtime error detected:\n{message}")

    async def _safe_send_telegram(self, telegram, message: str) -> bool:
        try:
            return await self.telegram.send_message(telegram, message)
        except Exception:  # pragma: no cover
            return False
