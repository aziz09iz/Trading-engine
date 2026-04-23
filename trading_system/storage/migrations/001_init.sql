CREATE TABLE IF NOT EXISTS market_ticks (
    ts TIMESTAMPTZ NOT NULL,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    bid DOUBLE PRECISION,
    ask DOUBLE PRECISION,
    mid DOUBLE PRECISION,
    spread_bps DOUBLE PRECISION,
    PRIMARY KEY (ts, exchange, symbol)
);

CREATE TABLE IF NOT EXISTS funding_rates (
    ts TIMESTAMPTZ NOT NULL,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    current_rate DOUBLE PRECISION,
    predicted_rate DOUBLE PRECISION,
    PRIMARY KEY (ts, exchange, symbol)
);

CREATE TABLE IF NOT EXISTS features (
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    payload JSONB NOT NULL,
    PRIMARY KEY (ts, symbol)
);

CREATE TABLE IF NOT EXISTS signals (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    strategy TEXT NOT NULL,
    strength DOUBLE PRECISION NOT NULL,
    reason TEXT NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    price DOUBLE PRECISION,
    size DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL,
    exchange_order_id TEXT,
    client_order_id TEXT UNIQUE,
    signal_id BIGINT REFERENCES signals(id)
);
