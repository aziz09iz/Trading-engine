import { useEffect, useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const fundingRows = [
  {
    symbol: "BTC",
    funding: "0.018%",
    predicted: "0.031%",
    oiDelta: "+4.8%",
    cvd: "+18.4M",
    alignment: "87",
    signal: "LONG",
    strength: 0.88,
  },
  {
    symbol: "ETH",
    funding: "0.024%",
    predicted: "0.019%",
    oiDelta: "-1.2%",
    cvd: "-6.1M",
    alignment: "74",
    signal: "SHORT",
    strength: 0.76,
  },
  {
    symbol: "SOL",
    funding: "0.041%",
    predicted: "0.038%",
    oiDelta: "-3.6%",
    cvd: "-12.7M",
    alignment: "69",
    signal: "MR SHORT",
    strength: 0.8,
  },
  {
    symbol: "HYPE",
    funding: "0.012%",
    predicted: "0.013%",
    oiDelta: "+0.5%",
    cvd: "+1.2M",
    alignment: "58",
    signal: "WAIT",
    strength: 0.46,
  },
];

const positions = [
  { symbol: "BTC", side: "Long", notional: "$18,400", entry: "$101,240", pnl: "+$284", risk: "0.42%" },
  { symbol: "SOL", side: "Short", notional: "$9,800", entry: "$148.30", pnl: "-$46", risk: "0.31%" },
];

const orders = [
  { symbol: "BTC", side: "Buy", type: "Alo limit", price: "$101,080", status: "resting" },
  { symbol: "ETH", side: "Sell", type: "Alo limit", price: "$3,286", status: "watching" },
  { symbol: "SOL", side: "Sell", type: "reduce tp1", price: "$145.20", status: "queued" },
];

function classNames(...items) {
  return items.filter(Boolean).join(" ");
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

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/health`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error("bad response"))))
      .then(() => {
        if (!cancelled) setHealth("online");
      })
      .catch(() => {
        if (!cancelled) setHealth("offline");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const exposure = useMemo(() => {
    return positions.reduce((sum, row) => sum + Number(row.notional.replace(/[$,]/g, "")), 0);
  }, []);

  async function toggleEngine() {
    const nextPaused = !enginePaused;
    const action = nextPaused ? "pause" : "resume";
    setActionPending(true);
    try {
      await fetch(`${API_URL}/engine/${action}`, { method: "POST" });
      setEnginePaused(nextPaused);
    } catch {
      setHealth("offline");
    } finally {
      setActionPending(false);
    }
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
            >
              Reduce Only
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
          <Metric label="Equity" value="$100,000" detail="Shadow account baseline" />
          <Metric label="Exposure" value={`$${exposure.toLocaleString()}`} detail="28.2% of max allocation" tone="warn" />
          <Metric label="Daily PnL" value="+$238" detail="Drawdown stop at -3.0%" tone="good" />
          <Metric label="Open Risk" value="0.73%" detail="Across 2 positions" tone="neutral" />
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
                {fundingRows.map((row) => (
                  <tr className="hover:bg-white/[0.03]" key={row.symbol}>
                    <td className="px-4 py-4 font-semibold">{row.symbol}</td>
                    <td className="px-4 py-4 font-mono text-stone-300">{row.funding}</td>
                    <td className="px-4 py-4 font-mono text-stone-300">{row.predicted}</td>
                    <td className="px-4 py-4 font-mono text-stone-300">{row.oiDelta}</td>
                    <td className="px-4 py-4 font-mono text-stone-300">{row.cvd}</td>
                    <td className="px-4 py-4 font-mono text-stone-300">{row.alignment}</td>
                    <td className="px-4 py-4">
                      <SignalBadge value={row.signal} />
                    </td>
                    <td className="px-4 py-4">
                      <StrengthBar value={row.strength} />
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
                ["Concurrent positions", "2 / 6", "w-4/12", "bg-emerald-300"],
                ["Daily drawdown", "0.24% / 3%", "w-1/12", "bg-amber-300"],
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
              {orders.map((order) => (
                <div className="rounded-md border border-white/10 bg-stone-950 p-3" key={`${order.symbol}-${order.price}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">{order.symbol}</span>
                    <span className="rounded bg-stone-800 px-2 py-1 text-xs text-stone-300">{order.status}</span>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-stone-400">
                    <span>{order.side}</span>
                    <span>{order.type}</span>
                    <span className="text-right font-mono text-stone-200">{order.price}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </aside>

        <section className="rounded-lg border border-white/10 bg-zinc-950/80 shadow-glow lg:col-span-12">
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
            <h2 className="font-semibold">Open Positions</h2>
            <span className="text-xs text-stone-500">ATR stops and staged exits active</span>
          </div>
          <div className="grid gap-3 p-4 md:grid-cols-2">
            {positions.map((position) => (
              <div className="rounded-lg border border-white/10 bg-stone-950 p-4" key={position.symbol}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-lg font-semibold">{position.symbol}</p>
                    <p className="text-sm text-stone-500">{position.side} perpetual</p>
                  </div>
                  <span
                    className={classNames(
                      "rounded-md px-2 py-1 text-xs font-semibold",
                      position.side === "Long"
                        ? "bg-emerald-400/10 text-emerald-200"
                        : "bg-rose-400/10 text-rose-200",
                    )}
                  >
                    {position.pnl}
                  </span>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
                  <div>
                    <p className="text-stone-500">Notional</p>
                    <p className="mt-1 font-mono">{position.notional}</p>
                  </div>
                  <div>
                    <p className="text-stone-500">Entry</p>
                    <p className="mt-1 font-mono">{position.entry}</p>
                  </div>
                  <div>
                    <p className="text-stone-500">Risk</p>
                    <p className="mt-1 font-mono">{position.risk}</p>
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
