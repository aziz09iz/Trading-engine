from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class HyperliquidCredentials(BaseModel):
    account_address: str = ""
    secret_key: str = ""
    api_url: str = "https://api.hyperliquid.xyz"
    ws_url: str = "wss://api.hyperliquid.xyz/ws"


class TelegramSettings(BaseModel):
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""
    notify_api_status: bool = True
    notify_engine_actions: bool = True
    notify_trade_activity: bool = True
    notify_pnl_summary: bool = True
    notify_errors: bool = True
    summary_interval_minutes: int = 60


class TradingParameters(BaseModel):
    max_total_exposure_pct: float = 0.30
    max_concurrent_positions: int = 6
    daily_drawdown_stop_pct: float = 0.03
    min_risk_pct: float = 0.0025
    max_risk_pct: float = 0.0075
    max_spread_bps: float = 5.0
    top_n_markets: int = 10
    refresh_seconds: int = 60
    execution_cooldown_seconds: int = 300
    shadow_mode: bool = True
    reduce_only_mode: bool = False
    atr_stop_min: float = 1.2
    atr_stop_max: float = 2.0


class UserSettings(BaseModel):
    hyperliquid: HyperliquidCredentials = Field(default_factory=HyperliquidCredentials)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    trading: TradingParameters = Field(default_factory=TradingParameters)


class UserSettingsUpdate(BaseModel):
    hyperliquid: HyperliquidCredentials | None = None
    telegram: TelegramSettings | None = None
    trading: TradingParameters | None = None


class SettingsStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self._settings = UserSettings()
        self.load()

    @property
    def settings(self) -> UserSettings:
        return self._settings

    def load(self) -> UserSettings:
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self._settings = UserSettings.model_validate(payload)
            self.save()
        else:
            self.save()
        return self._settings

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            self._settings.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def update(self, update: UserSettingsUpdate) -> UserSettings:
        current = self._settings.model_copy(deep=True)
        if update.hyperliquid is not None:
            current_hl = current.hyperliquid.model_dump()
            incoming_hl = update.hyperliquid.model_dump()
            if not incoming_hl.get("secret_key"):
                incoming_hl["secret_key"] = current.hyperliquid.secret_key
            current.hyperliquid = HyperliquidCredentials(**(current_hl | incoming_hl))
        if update.telegram is not None:
            current_tg = current.telegram.model_dump()
            incoming_tg = update.telegram.model_dump()
            if not incoming_tg.get("bot_token"):
                incoming_tg["bot_token"] = current.telegram.bot_token
            current.telegram = TelegramSettings(**(current_tg | incoming_tg))
        if update.trading is not None:
            current.trading = update.trading
        self._settings = current
        self.save()
        return self._settings

    def public_payload(self) -> dict[str, object]:
        payload = self._settings.model_dump()
        payload["hyperliquid"]["secret_key"] = ""
        payload["hyperliquid"]["has_secret_key"] = bool(self._settings.hyperliquid.secret_key)
        payload["telegram"]["bot_token"] = ""
        payload["telegram"]["has_bot_token"] = bool(self._settings.telegram.bot_token)
        return payload
