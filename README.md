# Hyperliquid Funding Arbitrage Engine

Async Python trading system skeleton for Hyperliquid perpetual futures using funding pressure, open interest, CVD, positioning skew, and cross-exchange predicted funding.

This repository is an implementation scaffold, not financial advice and not a turnkey profitable strategy.

## Core Components

- `trading_system/data`: exchange ingestion adapters and top-10 liquidity universe selection.
- `trading_system/features`: funding, OI, CVD, trend, ATR, and microstructure features.
- `trading_system/signals`: continuation and mean-reversion scoring on funding, positioning, order flow, cross-exchange alignment, and trend.
- `trading_system/risk`: position sizing and portfolio limits.
- `trading_system/execution`: adaptive limit order planning and Hyperliquid execution adapter.
- `trading_system/backtest`: historical replay broker and metrics.
- `trading_system/app`: FastAPI control plane.
- `frontend`: React + Tailwind trading dashboard.

## Trading Logic

The engine is designed around the top 10 Hyperliquid markets by liquidity and volume, not a fixed manual watchlist.

Every market is scored from:

- current funding rate
- predicted next funding rate
- rate persistence
- funding microstructure momentum
- CVD
- long/short ratio
- OI delta
- OI absolute level relative to history
- cross-exchange predicted funding alignment
- ATR and MA trend context

Continuation trades follow the crowded side only when funding, OI expansion, CVD, and trend all agree.
Mean reversion trades fade the crowd only when funding is extreme, positioning is skewed, OI stops expanding, and CVD diverges.

Risk is dynamic:

- weak-valid setup: near minimum risk
- strong confluence plus high liquidity: higher risk
- mean reversion gets slightly less risk than continuation at the same conviction
- high spread and portfolio constraints still veto trades

## Live Runtime

The API now maintains a live engine snapshot that:

- fetches Hyperliquid market state from the official `info` endpoint
- selects the top 10 liquid perpetuals
- stores rolling open-interest history locally and computes `oi_zscore`
- ranks trade candidates and produces a live dashboard payload

Available endpoints:

- `GET /dashboard/overview`
- `POST /engine/refresh`
- `POST /engine/pause`
- `POST /engine/resume`
- `GET /settings`
- `PUT /settings`

Dashboard settings now support:

- Hyperliquid account address
- Hyperliquid secret key
- API and WebSocket URLs
- maximum exposure
- maximum concurrent positions
- daily drawdown stop
- min/max risk per trade
- max spread filter
- top market count
- refresh interval
- shadow mode and reduce-only mode

Current note:

- open interest and funding are live from Hyperliquid
- top-10 universe selection is live from Hyperliquid
- `oi_zscore` is computed from locally accumulated runtime history
- CVD and long/short ratio remain derived proxies until the trade stream and external positioning sources are fully wired

## Quick Start

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e ".[dev]"
pytest
uvicorn trading_system.app.main:app --reload
```

## Tailwind Dashboard

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` if the FastAPI service is not running on `http://localhost:8000`.

## Docker

```bash
docker compose up --build
```

## Safety Defaults

- Maximum exposure: 30% of equity.
- Maximum concurrent positions: 6.
- Daily drawdown stop: 3%.
- Risk per trade: 0.25% to 0.75% of equity.
- Adaptive limit entries reject high-spread markets.

Run shadow mode and tiny sizing before connecting live execution.
