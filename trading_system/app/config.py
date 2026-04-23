from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "development"
    hyperliquid_api_url: str = "https://api.hyperliquid.xyz"
    hyperliquid_ws_url: str = "wss://api.hyperliquid.xyz/ws"
    database_url: str = "postgresql+asyncpg://trading:trading_password@postgres:5432/trading"
    redis_url: str = "redis://redis:6379/0"
    max_total_exposure_pct: float = 0.30
    max_concurrent_positions: int = 6
    daily_drawdown_stop_pct: float = 0.03

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
