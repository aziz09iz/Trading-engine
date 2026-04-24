import { useEffect, useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function classNames(...items) {
  return items.filter(Boolean).join(" ");
}

function formatUsd(value) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(
    Number(value ?? 0),
  );
}

function formatPct(value, digits = 2) {
  return `${(Number(value ?? 0) * 100).toFixed(digits)}%`;
}

function Input({ label, value, onChange, type = "text", placeholder = "", step }) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs uppercase text-stone-500">{label}</span>
      <input
        className="w-full rounded-md border border-white/10 bg-stone-950 px-3 py-2 text-sm text-stone-100 outline-none ring-0 placeholder:text-stone-600 focus:border-cyan-300/40"
        onChange={onChange}
        placeholder={placeholder}
        step={step}
        type={type}
        value={value}
      />
    </label>
  );
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="flex items-center justify-between rounded-md border border-white/10 bg-stone-950 px-3 py-2">
      <span className="text-sm text-stone-300">{label}</span>
      <button
        className={classNames(
          "relative h-6 w-11 rounded-full transition-colors",
          checked ? "bg-emerald-300" : "bg-stone-700",
        )}
        onClick={onChange}
        type="button"
      >
        <span
          className={classNames(
            "absolute top-1 h-4 w-4 rounded-full bg-stone-950 transition-transform",
            checked ? "translate-x-6" : "translate-x-1",
          )}
        />
      </button>
    </label>
  );
}

function StatusPill({ status }) {
  const palette = {
    live: "border-emerald-400/30 bg-emerald-400/10 text-emerald-200",
    paused: "border-amber-300/30 bg-amber-300/10 text-amber-100",
    danger: "border-rose-400/30 bg-rose-400/10 text-rose-100",
  };
  return (
    <span className={classNames("rounded-full border px-3 py-1 text-xs font-medium", palette[status])}>
      {status.toUpperCase()}
    </span>
  );
}

function Metric({ label, value, detail, tone = "neutral" }) {
  const tones = {
    neutral: "text-stone-100",
    good: "text-emerald-200",
    warn: "text-amber-100",
    bad: "text-rose-100",
  };
  return (
    <div className="rounded-lg border border-white/10 bg-zinc-950/80 p-4 shadow-glow">
      <p className="text-xs uppercase text-stone-500">{label}</p>
      <div className={classNames("mt-3 text-2xl font-semibold", tones[tone])}>{value}</div>
      <p className="mt-2 text-sm text-stone-400">{detail}</p>
    </div>
  );
}

function StrengthBar({ value }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.85 ? "bg-emerald-300" : value >= 0.7 ? "bg-cyan-300" : "bg-stone-500";
  return (
    <div className="flex min-w-32 items-center gap-3">
      <div className="h-2 w-24 rounded-full bg-stone-800">
        <div className={classNames("h-2 rounded-full", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-xs text-stone-300">{pct}</span>
    </div>
  );
}

function SignalBadge({ value }) {
  const isLong = value.includes("LONG");
  const isShort = value.includes("SHORT");
  return (
    <span
      className={classNames(
        "rounded-md px-2 py-1 text-xs font-semibold",
        isLong && "bg-emerald-400/10 text-emerald-200",
        isShort && "bg-rose-400/10 text-rose-200",
        !isLong && !isShort && "bg-stone-800 text-stone-300",
      )}
    >
      {value}
    </span>
  );
}

function App() {
  const [enginePaused, setEnginePaused] = useState(true);
  const [health, setHealth] = useState("checking");
  const [actionPending, setActionPending] = useState(false);
  const [overview, setOverview] = useState({
    metrics: {},
    signals: [],
    orders: [],
    universe: [],
    last_error: null,
    settings: {
      hyperliquid: {},
      trading: {},
    },
  });
  const [settingsDraft, setSettingsDraft] = useState({
    hyperliquid: {
      account_address: "",
      secret_key: "",
      api_url: "https://api.hyperliquid.xyz",
      ws_url: "wss://api.hyperliquid.xyz/ws",
      has_secret_key: false,
    },
    trading: {
      max_total_exposure_pct: 0.3,
      max_concurrent_positions: 6,
      daily_drawdown_stop_pct: 0.03,
      min_risk_pct: 0.0025,
      max_risk_pct: 0.0075,
      max_spread_bps: 5,
      top_n_markets: 10,
      refresh_seconds: 60,
      shadow_mode: true,
      reduce_only_mode: false,
      atr_stop_min: 1.2,
      atr_stop_max: 2.0,
    },
  });
  const [settingsPending, setSettingsPending] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [healthRes, overviewRes] = await Promise.all([
          fetch(`${API_URL}/health`),
          fetch(`${API_URL}/dashboard/overview`),
        ]);
        if (!healthRes.ok || !overviewRes.ok) {
          throw new Error("bad response");
        }
        const overviewPayload = await overviewRes.json();
        if (!cancelled) {
          setHealth("online");
          setEnginePaused(Boolean(overviewPayload.paused));
          setOverview(overviewPayload);
          setSettingsDraft(overviewPayload.settings);
        }
      } catch {
        if (!cancelled) setHealth("offline");
      }
    }

    load();
    const intervalId = window.setInterval(load, 15000);
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  const exposure = useMemo(() => {
    return Number(overview.metrics.current_exposure_pct ?? 0) * Number(overview.metrics.equity_usd ?? 0);
  }, [overview.metrics]);

  async function toggleEngine() {
    const nextPaused = !enginePaused;
    const action = nextPaused ? "pause" : "resume";
    setActionPending(true);
    try {
      await fetch(`${API_URL}/engine/${action}`, { method: "POST" });
      setEnginePaused(nextPaused);
      const response = await fetch(`${API_URL}/dashboard/overview`);
      if (response.ok) {
        const payload = await response.json();
        setOverview(payload);
        setSettingsDraft(payload.settings);
      }
    } catch {
      setHealth("offline");
    } finally {
      setActionPending(false);
    }
  }

  async function saveSettings() {
    setSettingsPending(true);
    try {
      const response = await fetch(`${API_URL}/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settingsDraft),
      });
      if (!response.ok) {
        throw new Error("settings update failed");
      }
      const overviewResponse = await fetch(`${API_URL}/dashboard/overview`);
      if (!overviewResponse.ok) {
        throw new Error("overview refresh failed");
      }
      const payload = await overviewResponse.json();
      setOverview(payload);
      setSettingsDraft(payload.settings);
    } catch {
      setHealth("offline");
    } finally {
      setSettingsPending(false);
    }
  }

  function updateHyperliquidField(field, value) {
    setSettingsDraft((current) => ({
      ...current,
      hyperliquid: {
        ...current.hyperliquid,
        [field]: value,
      },
    }));
  }

  function updateTradingField(field, value) {
    setSettingsDraft((current) => ({
      ...current,
      trading: {
        ...current.trading,
        [field]: value,
      },
    }));
  }

  return (
    <main className="min-h-screen bg-[#11100e] text-stone-100">
      <div className="border-b border-white/10 bg-stone-950/95">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-xl font-semibold">Trading Engine</h1>
              <StatusPill status={enginePaused ? "paused" : "live"} />
              <span className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs text-cyan-100">
                API {health}
              </span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-stone-300">
                Universe top 10 liquid
              </span>
            </div>
            <p className="mt-1 text-sm text-stone-400">
              Hyperliquid funding, positioning, order flow, cross-exchange alignment, and dynamic risk.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              className="rounded-md border border-white/10 bg-stone-900 px-4 py-2 text-sm text-stone-200 hover:bg-stone-800"
              type="button"
              onClick={() => updateTradingField("reduce_only_mode", !settingsDraft.trading.reduce_only_mode)}
            >
              {settingsDraft.trading.reduce_only_mode ? "Reduce Only On" : "Reduce Only Off"}
            </button>
            <button
              className={classNames(
                "rounded-md px-4 py-2 text-sm font-semibold",
                actionPending && "cursor-wait opacity-70",
                enginePaused
                  ? "bg-emerald-300 text-stone-950 hover:bg-emerald-200"
                  : "bg-amber-300 text-stone-950 hover:bg-amber-200",
              )}
              type="button"
              disabled={actionPending}
              onClick={toggleEngine}
            >
              {actionPending ? "Working" : enginePaused ? "Resume Engine" : "Pause Engine"}
            </button>
          </div>
        </div>
      </div>

      <div className="mx-auto grid max-w-7xl gap-5 px-4 py-6 sm:px-6 lg:grid-cols-12">
        <section className="grid gap-4 lg:col-span-12 lg:grid-cols-4">
          <Metric label="Equity" value={formatUsd(overview.metrics.equity_usd)} detail="Engine account baseline" />
          <Metric
            label="Exposure"
            value={formatUsd(exposure)}
            detail={`${formatPct(overview.metrics.current_exposure_pct)} of max allocation`}
            tone="warn"
          />
          <Metric
            label="Daily PnL"
            value={formatUsd(overview.metrics.daily_pnl_usd)}
            detail="Drawdown stop at -3.0%"
            tone={Number(overview.metrics.daily_pnl_usd ?? 0) >= 0 ? "good" : "bad"}
          />
          <Metric
            label="Open Risk"
            value={formatPct(overview.metrics.open_risk_pct)}
            detail={`Across ${overview.orders.length} queued trades`}
            tone="neutral"
          />
        </section>

        <section className="rounded-lg border border-white/10 bg-zinc-950/80 shadow-glow lg:col-span-8">
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
            <h2 className="font-semibold">Funding Signal Board</h2>
            <span className="font-mono text-xs text-stone-500">thresholds 0.70 / 0.85</span>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase text-stone-500">
                <tr>
                  {["Symbol", "Funding", "Predicted", "OI Delta", "CVD", "Alignment", "Signal", "Strength"].map(
                    (head) => (
                      <th className="px-4 py-3 font-medium" key={head}>
                        {head}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {overview.signals.map((row) => (
                  <tr className="hover:bg-white/[0.03]" key={row.symbol}>
                    <td className="px-4 py-4 font-semibold">{row.symbol}</td>
                    <td className="px-4 py-4 font-mono text-stone-300">{formatPct(row.funding, 3)}</td>
                    <td className="px-4 py-4 font-mono text-stone-300">{formatPct(row.predicted_funding, 3)}</td>
                    <td className="px-4 py-4 font-mono text-stone-300">{formatPct(row.oi_delta)}</td>
                    <td className="px-4 py-4 font-mono text-stone-300">{formatUsd(row.cvd)}</td>
                    <td className="px-4 py-4 font-mono text-stone-300">{Math.round((row.alignment ?? 0) * 100)}</td>
                    <td className="px-4 py-4">
                      <SignalBadge value={`${row.strategy} ${row.side}`.toUpperCase()} />
                    </td>
                    <td className="px-4 py-4">
                      <StrengthBar value={Number(row.strength ?? 0)} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="grid gap-5 lg:col-span-4">
          <section className="rounded-lg border border-white/10 bg-zinc-950/80 p-4 shadow-glow">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Risk Guard</h2>
              <StatusPill status="live" />
            </div>
            <div className="mt-5 space-y-4">
              {[
                ["Max exposure", "30%", "w-7/12", "bg-cyan-300"],
                [`Concurrent positions`, `${overview.orders.length} / 6`, "w-4/12", "bg-emerald-300"],
                ["Daily drawdown", `${formatPct(Math.abs((overview.metrics.daily_pnl_usd ?? 0) / (overview.metrics.equity_usd ?? 1)))} / 3%`, "w-1/12", "bg-amber-300"],
                ["Dynamic risk", "0.25% to 0.75%", "w-3/12", "bg-violet-300"],
              ].map(([label, value, width, color]) => (
                <div key={label}>
                  <div className="mb-2 flex justify-between text-sm">
                    <span className="text-stone-400">{label}</span>
                    <span className="font-mono text-stone-200">{value}</span>
                  </div>
                  <div className="h-2 rounded-full bg-stone-800">
                    <div className={classNames("h-2 rounded-full", width, color)} />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-white/10 bg-zinc-950/80 p-4 shadow-glow">
            <h2 className="font-semibold">Execution Queue</h2>
            <div className="mt-4 space-y-3">
              {overview.orders.map((order) => (
                <div className="rounded-md border border-white/10 bg-stone-950 p-3" key={`${order.symbol}-${order.price}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">{order.symbol}</span>
                    <span className="rounded bg-stone-800 px-2 py-1 text-xs text-stone-300">{order.status}</span>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-stone-400">
                    <span>{order.side}</span>
                    <span>{order.type}</span>
                    <span className="text-right font-mono text-stone-200">{formatUsd(order.price)}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </aside>

        <section className="rounded-lg border border-white/10 bg-zinc-950/80 shadow-glow lg:col-span-12">
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
            <h2 className="font-semibold">Settings</h2>
            <button
              className={classNames(
                "rounded-md px-4 py-2 text-sm font-semibold",
                settingsPending ? "bg-stone-700 text-stone-300" : "bg-cyan-300 text-stone-950 hover:bg-cyan-200",
              )}
              disabled={settingsPending}
              onClick={saveSettings}
              type="button"
            >
              {settingsPending ? "Saving" : "Save Settings"}
            </button>
          </div>
          <div className="grid gap-5 p-4 lg:grid-cols-2">
            <div className="space-y-4">
              <h3 className="text-sm font-semibold uppercase text-stone-400">Hyperliquid</h3>
              <Input
                label="Account Address"
                onChange={(event) => updateHyperliquidField("account_address", event.target.value)}
                placeholder="0x..."
                value={settingsDraft.hyperliquid.account_address ?? ""}
              />
              <Input
                label="Secret Key"
                onChange={(event) => updateHyperliquidField("secret_key", event.target.value)}
                placeholder={settingsDraft.hyperliquid.has_secret_key ? "Stored secret retained if left blank" : "Enter secret key"}
                value={settingsDraft.hyperliquid.secret_key ?? ""}
              />
              <Input
                label="API URL"
                onChange={(event) => updateHyperliquidField("api_url", event.target.value)}
                value={settingsDraft.hyperliquid.api_url ?? ""}
              />
              <Input
                label="WebSocket URL"
                onChange={(event) => updateHyperliquidField("ws_url", event.target.value)}
                value={settingsDraft.hyperliquid.ws_url ?? ""}
              />
            </div>

            <div className="space-y-4">
              <h3 className="text-sm font-semibold uppercase text-stone-400">Trading Controls</h3>
              <div className="grid gap-4 md:grid-cols-2">
                <Input
                  label="Maximum Exposure"
                  onChange={(event) => updateTradingField("max_total_exposure_pct", Number(event.target.value))}
                  step="0.01"
                  type="number"
                  value={settingsDraft.trading.max_total_exposure_pct ?? 0}
                />
                <Input
                  label="Max Concurrent Positions"
                  onChange={(event) => updateTradingField("max_concurrent_positions", Number(event.target.value))}
                  step="1"
                  type="number"
                  value={settingsDraft.trading.max_concurrent_positions ?? 0}
                />
                <Input
                  label="Daily Drawdown Stop"
                  onChange={(event) => updateTradingField("daily_drawdown_stop_pct", Number(event.target.value))}
                  step="0.001"
                  type="number"
                  value={settingsDraft.trading.daily_drawdown_stop_pct ?? 0}
                />
                <Input
                  label="Min Risk Per Trade"
                  onChange={(event) => updateTradingField("min_risk_pct", Number(event.target.value))}
                  step="0.0005"
                  type="number"
                  value={settingsDraft.trading.min_risk_pct ?? 0}
                />
                <Input
                  label="Max Risk Per Trade"
                  onChange={(event) => updateTradingField("max_risk_pct", Number(event.target.value))}
                  step="0.0005"
                  type="number"
                  value={settingsDraft.trading.max_risk_pct ?? 0}
                />
                <Input
                  label="Max Spread Bps"
                  onChange={(event) => updateTradingField("max_spread_bps", Number(event.target.value))}
                  step="0.1"
                  type="number"
                  value={settingsDraft.trading.max_spread_bps ?? 0}
                />
                <Input
                  label="Top Markets"
                  onChange={(event) => updateTradingField("top_n_markets", Number(event.target.value))}
                  step="1"
                  type="number"
                  value={settingsDraft.trading.top_n_markets ?? 10}
                />
                <Input
                  label="Refresh Seconds"
                  onChange={(event) => updateTradingField("refresh_seconds", Number(event.target.value))}
                  step="1"
                  type="number"
                  value={settingsDraft.trading.refresh_seconds ?? 60}
                />
                <Input
                  label="ATR Stop Min"
                  onChange={(event) => updateTradingField("atr_stop_min", Number(event.target.value))}
                  step="0.1"
                  type="number"
                  value={settingsDraft.trading.atr_stop_min ?? 1.2}
                />
                <Input
                  label="ATR Stop Max"
                  onChange={(event) => updateTradingField("atr_stop_max", Number(event.target.value))}
                  step="0.1"
                  type="number"
                  value={settingsDraft.trading.atr_stop_max ?? 2}
                />
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <Toggle
                  checked={Boolean(settingsDraft.trading.shadow_mode)}
                  label="Shadow Mode"
                  onChange={() => updateTradingField("shadow_mode", !settingsDraft.trading.shadow_mode)}
                />
                <Toggle
                  checked={Boolean(settingsDraft.trading.reduce_only_mode)}
                  label="Reduce Only Mode"
                  onChange={() => updateTradingField("reduce_only_mode", !settingsDraft.trading.reduce_only_mode)}
                />
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-white/10 bg-zinc-950/80 shadow-glow lg:col-span-12">
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
            <h2 className="font-semibold">Top 10 Liquid Universe</h2>
            <span className="text-xs text-stone-500">Live selection for engine analysis</span>
          </div>
          <div className="grid gap-3 p-4 md:grid-cols-2">
            {overview.universe.map((position) => (
              <div className="rounded-lg border border-white/10 bg-stone-950 p-4" key={position.symbol}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-lg font-semibold">{position.symbol}</p>
                    <p className="text-sm text-stone-500">Perpetual candidate</p>
                  </div>
                  <span className="rounded-md bg-cyan-400/10 px-2 py-1 text-xs font-semibold text-cyan-200">
                    {formatPct((position.spread_bps ?? 0) / 10000, 2)} spread
                  </span>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
                  <div>
                    <p className="text-stone-500">24h volume</p>
                    <p className="mt-1 font-mono">{formatUsd(position.volume_24h)}</p>
                  </div>
                  <div>
                    <p className="text-stone-500">Open interest</p>
                    <p className="mt-1 font-mono">{formatUsd(position.open_interest_usd)}</p>
                  </div>
                  <div>
                    <p className="text-stone-500">Spread</p>
                    <p className="mt-1 font-mono">{Number(position.spread_bps ?? 0).toFixed(2)} bps</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

export default App;
