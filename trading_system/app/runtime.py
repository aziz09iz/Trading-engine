from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from time import time

from trading_system.app.config import settings
from trading_system.app.user_settings import SettingsStore, UserSettings, UserSettingsUpdate
from trading_system.data.hyperliquid_info import HyperliquidInfoClient
from trading_system.execution.live_executor import ExecutionResult, LiveExecutionService
from trading_system.features.oi_history import OpenInterestHistory
from trading_system.risk.sizing import AccountState, SizingConfig, position_size_usd, risk_pct_for_signal
from trading_system.signals.engine import rank_trade_candidates
from trading_system.signals.models import TradeSignal


@dataclass
class EngineSnapshot:
    paused: bool = True
    last_error: str | None = None
    generated_at: float | None = None
    universe: list[dict[str, object]] = field(default_factory=list)
    signals: list[dict[str, object]] = field(default_factory=list)
    orders: list[dict[str, object]] = field(default_factory=list)
    metrics: dict[str, object] = field(default_factory=dict)


class TradingRuntime:
    def __init__(self) -> None:
        self.settings_store = SettingsStore(settings.runtime_settings_path)
        self.client = HyperliquidInfoClient(self.user_settings.hyperliquid.api_url)
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
        self._task: asyncio.Task | None = None

    @property
    def user_settings(self) -> UserSettings:
        return self.settings_store.settings

    def update_settings(self, update: UserSettingsUpdate) -> UserSettings:
        updated = self.settings_store.update(update)
        self.client = HyperliquidInfoClient(updated.hyperliquid.api_url)
        return updated

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

    async def _run(self) -> None:
        while True:
            try:
                await self.refresh()
            except Exception as exc:  # pragma: no cover
                self.snapshot.last_error = str(exc)
            await asyncio.sleep(self.user_settings.trading.refresh_seconds)

    async def refresh(self) -> EngineSnapshot:
        live = await self.client.fetch_market_snapshot(
            self.oi_history,
            top_n=self.user_settings.trading.top_n_markets,
        )
        eligible_markets = [
            market for market in live.markets if market.spread_bps <= self.user_settings.trading.max_spread_bps
        ]
        market_map = {row.symbol: row for row in eligible_markets}
        ranked = rank_trade_candidates(eligible_markets)
        orders = [self._make_order(signal, market_map=market_map) for signal in ranked[:6]]
        executed_orders = await self._execute_orders([order for order in orders if order], ranked[:6], market_map)
        self.snapshot = EngineSnapshot(
            paused=self.snapshot.paused,
            last_error=None,
            generated_at=time(),
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
            metrics=self._metrics_payload(ranked, eligible_markets),
        )
        return self.snapshot

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
        }

    def _make_order(self, signal: TradeSignal, market_map: dict[str, object]) -> dict[str, object] | None:
        market = market_map[signal.symbol]
        if signal.invalidation_price is None:
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
        return {
            "symbol": signal.symbol,
            "side": "Buy" if signal.side == "long" else "Sell",
            "type": f"{signal.strategy.value} limit",
            "price": market.mid_price,
            "notional_usd": notional,
            "risk_pct": risk_pct_for_signal(signal, config),
            "shadow_mode": self.user_settings.trading.shadow_mode,
            "reduce_only": self.user_settings.trading.reduce_only_mode,
            "status": "ready" if not self.snapshot.paused and not self.user_settings.trading.shadow_mode else "shadow",
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
            if self.snapshot.paused:
                order["status"] = "paused"
                order["message"] = "engine paused"
                executed.append(order)
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
            executed.append(order)
        return executed

    def _metrics_payload(self, ranked: list[TradeSignal], markets: list[object]) -> dict[str, object]:
        exposure = sum(order["notional_usd"] for order in [self._make_order(signal, {row.symbol: row for row in markets}) for signal in ranked[:6]] if order)
        return {
            "equity_usd": self.account.equity_usd,
            "daily_pnl_usd": self.account.daily_pnl_usd,
            "open_risk_pct": round(sum(signal.suggested_risk_pct for signal in ranked[:2]), 4),
            "max_exposure_pct": self.user_settings.trading.max_total_exposure_pct,
            "current_exposure_pct": round(exposure / self.account.equity_usd, 4) if self.account.equity_usd else 0.0,
            "signals_count": len(ranked),
            "tracked_markets": len(markets),
            "max_concurrent_positions": self.user_settings.trading.max_concurrent_positions,
            "daily_drawdown_stop_pct": self.user_settings.trading.daily_drawdown_stop_pct,
            "shadow_mode": self.user_settings.trading.shadow_mode,
            "reduce_only_mode": self.user_settings.trading.reduce_only_mode,
            "execution_cooldown_seconds": self.user_settings.trading.execution_cooldown_seconds,
        }
