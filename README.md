# Hyperliquid Funding Arbitrage Engine

Async Python trading system skeleton for Hyperliquid perpetual futures using funding pressure, open interest, CVD, positioning skew, and cross-exchange predicted funding.

This repository is an implementation scaffold, not financial advice and not a turnkey profitable strategy.

## Core Components

- `trading_system/data`: exchange ingestion adapters.
- `trading_system/features`: funding, OI, CVD, and microstructure features.
- `trading_system/signals`: continuation and mean-reversion signal scoring.
- `trading_system/risk`: position sizing and portfolio limits.
- `trading_system/execution`: adaptive limit order planning and Hyperliquid execution adapter.
- `trading_system/backtest`: historical replay broker and metrics.
- `trading_system/app`: FastAPI control plane.
- `frontend`: React + Tailwind trading dashboard.

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
