from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from trading_system.app.config import settings
from trading_system.app.runtime import TradingRuntime
from trading_system.app.user_settings import UserSettingsUpdate
from trading_system.storage.migrate import run_migrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime = TradingRuntime()
    app.state.runtime = runtime
    try:
        migrations_dir = Path(__file__).resolve().parents[1] / "storage" / "migrations"
        await run_migrations(settings.database_url, migrations_dir)
        runtime.set_migration_status(True)
    except Exception as exc:  # pragma: no cover
        runtime.set_migration_status(False, str(exc))
    try:
        await runtime.refresh()
    except Exception as exc:  # pragma: no cover
        runtime.snapshot.last_error = str(exc)
    await runtime.start()
    try:
        yield
    finally:
        await runtime.stop()


app = FastAPI(title="Hyperliquid Funding Arbitrage Engine", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, object]:
    runtime: TradingRuntime = app.state.runtime
    return {
        "status": "ok",
        "env": settings.env,
        "migration_ok": runtime.snapshot.migration_ok,
        "migration_error": runtime.snapshot.migration_error,
    }


@app.get("/")
async def root() -> dict[str, object]:
    runtime: TradingRuntime = app.state.runtime
    return {
        "service": "Hyperliquid Funding Arbitrage Engine",
        "status": "ok",
        "paused": runtime.snapshot.paused,
        "last_error": runtime.snapshot.last_error,
        "migration_ok": runtime.snapshot.migration_ok,
        "migration_error": runtime.snapshot.migration_error,
        "endpoints": {
            "health": "/health",
            "overview": "/dashboard/overview",
            "settings": "/settings",
            "telegram_test": "/settings/telegram/test",
        },
    }


@app.get("/risk")
async def risk_state() -> dict[str, float | int | bool]:
    runtime: TradingRuntime = app.state.runtime
    return {
        "daily_drawdown_stop": False,
        "max_exposure_pct": runtime.user_settings.trading.max_total_exposure_pct,
        "max_positions": runtime.user_settings.trading.max_concurrent_positions,
        "daily_drawdown_stop_pct": runtime.user_settings.trading.daily_drawdown_stop_pct,
        "paused": runtime.snapshot.paused,
    }


@app.post("/engine/pause")
async def pause_engine() -> dict[str, bool]:
    runtime: TradingRuntime = app.state.runtime
    runtime.snapshot.paused = True
    await runtime.notify_engine_action("paused")
    return {"paused": True}


@app.post("/engine/resume")
async def resume_engine() -> dict[str, bool]:
    runtime: TradingRuntime = app.state.runtime
    runtime.snapshot.paused = False
    await runtime.notify_engine_action("resumed")
    return {"paused": False}


@app.post("/engine/refresh")
async def refresh_engine() -> dict[str, object]:
    runtime: TradingRuntime = app.state.runtime
    snapshot = await runtime.refresh()
    return {
        "signals_count": len(snapshot.signals),
        "tracked_markets": len(snapshot.universe),
        "last_error": snapshot.last_error,
    }


@app.get("/dashboard/overview")
async def dashboard_overview() -> dict[str, object]:
    runtime: TradingRuntime = app.state.runtime
    return {
        "paused": runtime.snapshot.paused,
        "last_error": runtime.snapshot.last_error,
        "generated_at": runtime.snapshot.generated_at,
        "migration_ok": runtime.snapshot.migration_ok,
        "migration_error": runtime.snapshot.migration_error,
        "metrics": runtime.snapshot.metrics,
        "universe": runtime.snapshot.universe,
        "signals": runtime.snapshot.signals,
        "orders": runtime.snapshot.orders,
        "settings": runtime.settings_store.public_payload(),
    }


@app.get("/settings")
async def get_settings() -> dict[str, object]:
    runtime: TradingRuntime = app.state.runtime
    return runtime.settings_store.public_payload()


@app.put("/settings")
async def update_settings(update: UserSettingsUpdate) -> dict[str, object]:
    runtime: TradingRuntime = app.state.runtime
    runtime.update_settings(update)
    await runtime.refresh()
    await runtime.notify_engine_action("settings updated")
    return runtime.settings_store.public_payload()


@app.post("/settings/telegram/test")
async def test_telegram_settings() -> dict[str, object]:
    runtime: TradingRuntime = app.state.runtime
    sent = await runtime.send_telegram_test()
    return {"sent": sent}
