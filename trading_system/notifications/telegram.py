from __future__ import annotations

import httpx

from trading_system.app.user_settings import TelegramSettings


class TelegramNotifier:
    def enabled(self, settings: TelegramSettings) -> bool:
        return bool(settings.enabled and settings.bot_token and settings.chat_id)

    async def send_message(self, settings: TelegramSettings, message: str) -> bool:
        if not self.enabled(settings):
            return False

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{settings.bot_token}/sendMessage",
                json={
                    "chat_id": settings.chat_id,
                    "text": message,
                    "disable_web_page_preview": True,
                },
            )
            response.raise_for_status()
        return True
