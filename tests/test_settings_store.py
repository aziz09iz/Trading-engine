from trading_system.app.user_settings import SettingsStore, TradingParameters, TelegramSettings, UserSettingsUpdate


def test_settings_store_keeps_existing_secret_when_blank_update(tmp_path) -> None:
    store = SettingsStore(str(tmp_path / "settings.json"))
    store.update(
        UserSettingsUpdate(
            hyperliquid={
                "account_address": "0x123",
                "secret_key": "super-secret",
                "api_url": "https://api.hyperliquid.xyz",
                "ws_url": "wss://api.hyperliquid.xyz/ws",
            }
        )
    )

    store.update(
        UserSettingsUpdate(
            hyperliquid={
                "account_address": "0x456",
                "secret_key": "",
                "api_url": "https://api.hyperliquid.xyz",
                "ws_url": "wss://api.hyperliquid.xyz/ws",
            },
            trading=TradingParameters(max_concurrent_positions=4),
        )
    )

    assert store.settings.hyperliquid.secret_key == "super-secret"
    assert store.settings.hyperliquid.account_address == "0x456"
    assert store.settings.trading.max_concurrent_positions == 4


def test_settings_store_keeps_existing_telegram_token_when_blank_update(tmp_path) -> None:
    store = SettingsStore(str(tmp_path / "settings.json"))
    store.update(
        UserSettingsUpdate(
            telegram=TelegramSettings(
                enabled=True,
                bot_token="telegram-secret",
                chat_id="12345",
            )
        )
    )

    store.update(
        UserSettingsUpdate(
            telegram=TelegramSettings(
                enabled=True,
                bot_token="",
                chat_id="99999",
            )
        )
    )

    assert store.settings.telegram.bot_token == "telegram-secret"
    assert store.settings.telegram.chat_id == "99999"
