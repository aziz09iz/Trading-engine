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

## Main Features

- live top-10 market selection from Hyperliquid liquidity and volume
- funding continuation and mean-reversion signal engine
- dynamic risk sizing based on setup quality
- shadow mode for paper execution with real market data
- live order submission to Hyperliquid when shadow mode is disabled
- reduce-only mode for defensive order handling
- rolling OI history with `oi_zscore`
- runtime settings persistence
- Telegram bot notifications for engine status and trading activity
- Docker deployment with healthchecks and automatic migration startup

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
- Telegram bot token and chat id
- API and WebSocket URLs
- maximum exposure
- maximum concurrent positions
- daily drawdown stop
- min/max risk per trade
- max spread filter
- top market count
- refresh interval
- execution cooldown
- shadow mode and reduce-only mode
- Telegram notification toggles

Live execution notes:

- when `shadow_mode` is enabled, orders are ranked and staged but not sent
- when `shadow_mode` is disabled and credentials are present, the runtime can submit live limit orders
- submissions use a per-symbol cooldown to avoid duplicate orders every refresh cycle
- size and price are rounded conservatively to Hyperliquid lot-size and price-precision rules

## Settings Explained

### `shadow_mode`

`shadow_mode` means the engine does the full analysis, creates signals, sizes trades, and prepares orders, but does not actually send any order to Hyperliquid.

Use this when:

- validating signals
- checking dashboard behavior
- testing Telegram notifications
- confirming settings before enabling live trading

### `reduce_only_mode`

`reduce_only_mode` means any live order sent by the engine is marked reduce-only, so it can only reduce or close exposure and cannot increase a position.

Use this when:

- managing exits only
- running defensive mode after a problem
- verifying execution plumbing without letting the bot build new exposure

### `max_total_exposure_pct`

Maximum notional exposure the bot is allowed to deploy relative to account equity.

### `max_concurrent_positions`

Caps how many separate markets can be active at once.

### `daily_drawdown_stop_pct`

Stops new risk-taking when the running daily loss breaches the configured threshold.

### `min_risk_pct` and `max_risk_pct`

The engine scales position risk between these bounds depending on conviction and liquidity quality.

### `max_spread_bps`

Markets wider than this spread are excluded from signal generation and execution.

### `execution_cooldown_seconds`

Prevents duplicate live submissions on the same symbol across repeated refresh cycles.

### Telegram notifications

You can configure:

- API status notifications
- engine actions like pause, resume, and settings updates
- trade activity like submitted, blocked, or cooldown events
- PnL and engine summary heartbeat
- runtime errors

The bot can send:

- API online status
- migration status
- mode information such as shadow or live
- pause/resume/settings update events
- trade submission results
- current exposure
- daily PnL
- tracked markets and signal count
- top current signal
- runtime errors

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

In local development and GitHub Codespaces, the Vite dev server proxies `/api` to `http://127.0.0.1:8000` automatically.
Set `VITE_API_URL` only if you want to override that behavior.

## Docker

```bash
docker compose up --build
```

The compose file now works without a `.env` file. Runtime defaults are used unless you provide settings from the dashboard or container environment.

### Production Docker Mode

For Codespaces or VPS deployment:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

What this adds:

- healthchecks for API, dashboard, Redis, and Postgres
- automatic migration run during API startup
- persistent runtime settings and OI history under `./runtime`
- production-oriented published port for the dashboard via `APP_PORT`
- internal-only API/Redis/Postgres in the production override

Codespaces tip:

- forward the dashboard port from the active compose mode
- if using the base compose, use port `8501`
- if using production override, use port `80` or your configured `APP_PORT`

## Safety Defaults

- Maximum exposure: 30% of equity.
- Maximum concurrent positions: 6.
- Daily drawdown stop: 3%.
- Risk per trade: 0.25% to 0.75% of equity.
- Adaptive limit entries reject high-spread markets.

Run shadow mode and tiny sizing before connecting live execution.
