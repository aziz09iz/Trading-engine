# Hyperliquid Trading Engine

Production-oriented Hyperliquid perpetual futures engine with:

- top-50 liquidity universe
- funding continuation + unwind logic
- real Hyperliquid trade stream for CVD
- live account positions, open orders, and fills
- dynamic risk sizing
- Telegram notifications
- React + Tailwind operations dashboard
- Hyperliquid mainnet and testnet support

This project is an execution scaffold for systematic trading. It is not financial advice.

---

## Quick Start

### Docker only

```bash
docker compose up --build
```

Open:

- Dashboard: `http://localhost:8501`
- API: `http://localhost:8000`

If you want the production-style compose:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

### Local dev

Backend:

```bash
uvicorn trading_system.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

---

## Web App Features

- **Live signal board**  
  Funding, predicted funding, OI delta, real CVD delta, crowd ratio, and signal strength.

- **Live account panels**  
  Positions, open orders, recent fills, runtime activity.

- **Kill switch controls**  
  `Cancel all` and `Flatten all`.

- **Execution controls**  
  `shadow_mode`, `reduce_only_mode`, cooldown, spread filter, liquidity threshold, signal threshold.

- **Network support**  
  Switch between Hyperliquid `mainnet` and `testnet`.

- **Telegram integration**  
  Notifications for runtime state, trade activity, errors, and periodic summaries.

- **Bilingual UI**  
  English and Indonesian.

---

## Settings Explained

### `shadow_mode`

Engine analyzes markets, generates signals, sizes trades, and prepares execution, but does **not** send live orders.

Use it for:

- dry runs
- verifying signal quality
- testing Telegram
- validating settings before going live

### `reduce_only_mode`

All live orders are sent as reduce-only. The engine can close or reduce exposure, but cannot increase a position.

Use it for:

- exit-only mode
- emergency containment
- execution verification with minimal risk

### `max_total_exposure_pct`

Maximum portfolio exposure relative to account equity.

### `max_concurrent_positions`

Maximum number of simultaneous markets with active exposure.

### `daily_drawdown_stop_pct`

Stops new risk-taking when daily closed PnL breaches the configured loss limit.

### `min_risk_pct` / `max_risk_pct`

Risk band used by dynamic sizing. Stronger setups can size closer to `max_risk_pct`.

### `max_spread_bps`

Markets wider than this are rejected for signal generation and execution.

### `execution_cooldown_seconds`

Prevents repeated submissions on the same symbol every refresh cycle.

### `use_real_trade_stream`

Uses Hyperliquid real-time `trades` WebSocket feed to maintain live CVD and flow imbalance.

### `use_external_sentiment`

Uses external long/short ratio data instead of synthetic positioning proxies.

### `min_liquidity_score`

Rejects weaker markets even if they technically enter the top-N universe.

### `min_signal_strength`

Minimum score required before a candidate becomes tradable.

### `aggressive_signal_strength`

Signals above this threshold can receive larger dynamic risk allocation.

### `require_trend_alignment`

Keeps continuation entries aligned with MA structure and momentum filters.

### `require_cross_exchange_alignment`

Requires stronger agreement across Hyperliquid, Binance, and Bybit funding context.

---

## Telegram Notifications

Dashboard settings support:

- bot token
- chat id
- enable or disable notifications
- summary interval
- per-category toggles

The bot can send:

- API online status
- migration status
- settings updates
- cancel-all / flatten-all actions
- trade submission results
- blocked or cooldown events
- positions / open orders / exposure summary
- daily PnL summary
- runtime errors

---

## Trading Logic

The engine analyzes the **top 50 Hyperliquid markets by liquidity and volume**.

Signal inputs:

- current funding rate
- predicted funding rate
- rate persistence
- funding momentum
- microstructure momentum
- OI absolute level
- OI delta
- real CVD from Hyperliquid trades
- live long/short ratio feed
- cross-exchange funding alignment
- ATR
- MA structure

Entry logic emphasizes higher win-rate filtering by requiring stronger agreement across:

- funding regime
- crowd positioning
- OI expansion or unwind
- real order-flow confirmation
- spread and liquidity quality
- trend alignment

The result is fewer trades than a loose funding bot, but generally cleaner continuation and unwind setups.

---

## Notes

- Default universe is **50** markets.
- Dashboard no longer uses `Pause Engine`.
- Runtime is controlled through settings, `shadow_mode`, and kill switches.
- Healthchecks, startup migrations, and seeded runtime settings are already included in Docker.

---

## Bahasa Indonesia

## Mulai Cepat

### Jalankan full via Docker

```bash
docker compose up --build
```

Buka:

- Dashboard: `http://localhost:8501`
- API: `http://localhost:8000`

Mode production-like:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

## Fitur Web App

- papan sinyal live
- posisi live, open order, dan fill terbaru
- tombol `Cancel all` dan `Flatten all`
- mode `shadow` dan `reduce-only`
- support akun Hyperliquid `mainnet` dan `testnet`
- notifikasi Telegram
- dashboard dua bahasa: Inggris dan Indonesia

## Penjelasan Pengaturan Penting

### `shadow_mode`

Bot tetap analisa, hitung sizing, dan siapkan order, tapi **tidak** mengirim order live.

### `reduce_only_mode`

Semua order live hanya boleh mengurangi posisi yang sudah ada, tidak boleh menambah posisi baru.

### `max_total_exposure_pct`

Batas total eksposur terhadap equity akun.

### `daily_drawdown_stop_pct`

Jika rugi harian melewati batas ini, engine berhenti mengambil risiko baru.

### `use_real_trade_stream`

Menggunakan trade stream Hyperliquid real-time untuk menghitung CVD.

### `use_external_sentiment`

Menggunakan data rasio long/short eksternal yang live, bukan proxy sintetis.

### `min_signal_strength`

Sinyal di bawah ambang ini tidak akan dieksekusi.

## Telegram

Bot Telegram bisa mengirim:

- status API
- error runtime
- aktivitas trading
- hasil eksekusi
- ringkasan exposure dan PnL

## Catatan

- Universe default sekarang **top 50 pair**
- Fitur `Pause Engine` sudah dihapus
- Kontrol operasional utama sekarang: `shadow_mode`, `reduce_only_mode`, `Cancel all`, dan `Flatten all`
