from contextlib import asynccontextmanager

from fastapi import FastAPI

from trading_system.app.config import settings
from trading_system.app.runtime import TradingRuntime


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime = TradingRuntime()
    app.state.runtime = runtime
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}


@app.get("/risk")
async def risk_state() -> dict[str, float | int | bool]:
    runtime: TradingRuntime = app.state.runtime
    return {
        "daily_drawdown_stop": False,
        "max_exposure_pct": settings.max_total_exposure_pct,
        "max_positions": settings.max_concurrent_positions,
        "daily_drawdown_stop_pct": settings.daily_drawdown_stop_pct,
        "paused": runtime.snapshot.paused,
    }


@app.post("/engine/pause")
async def pause_engine() -> dict[str, bool]:
    runtime: TradingRuntime = app.state.runtime
    runtime.snapshot.paused = True
    return {"paused": True}


@app.post("/engine/resume")
async def resume_engine() -> dict[str, bool]:
    runtime: TradingRuntime = app.state.runtime
    runtime.snapshot.paused = False
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
        "metrics": runtime.snapshot.metrics,
        "universe": runtime.snapshot.universe,
        "signals": runtime.snapshot.signals,
        "orders": runtime.snapshot.orders,
    }
