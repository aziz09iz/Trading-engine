from fastapi import FastAPI

from trading_system.app.config import settings

app = FastAPI(title="Hyperliquid Funding Arbitrage Engine")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}


@app.get("/risk")
async def risk_state() -> dict[str, float | int | bool]:
    return {
        "daily_drawdown_stop": False,
        "max_exposure_pct": settings.max_total_exposure_pct,
        "max_positions": settings.max_concurrent_positions,
        "daily_drawdown_stop_pct": settings.daily_drawdown_stop_pct,
    }


@app.post("/engine/pause")
async def pause_engine() -> dict[str, bool]:
    return {"paused": True}


@app.post("/engine/resume")
async def resume_engine() -> dict[str, bool]:
    return {"paused": False}
