import { useEffect, useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "/api";

const copy = {
  en: {
    title: "Hyperliquid Trading Console",
    subtitle:
      "Funding, positioning, real trade-flow, cross-exchange alignment, dynamic risk, and Telegram notifications.",
    apiOnline: "API online",
    apiOffline: "API offline",
    migrationOk: "Migration ok",
    migrationPending: "Migration pending",
    topUniverse: "Top 50 liquid markets",
    executionShadow: "Execution shadow",
    executionLive: "Execution live",
    reduceOnlyOn: "Reduce-only on",
    reduceOnlyOff: "Reduce-only off",
    cancelAll: "Cancel all",
    flattenAll: "Flatten all",
    saveSettings: "Save settings",
    saving: "Saving",
    sendTelegramTest: "Send Telegram test",
    sending: "Sending",
    refreshNow: "Refresh now",
    nav: {
      dashboard: "Dashboard",
      pairs: "Pairs",
      settings: "Settings",
    },
    metrics: {
      equity: "Equity",
      exposure: "Exposure",
      withdrawable: "Withdrawable",
      dailyPnl: "Daily PnL",
      signals: "Signals",
      livePositions: "Live positions",
    },
    sections: {
      signals: "Funding Signal Board",
      positions: "Live Positions",
      openOrders: "Open Orders",
      fills: "Recent Fills",
      controls: "Kill Switch & Runtime",
      settings: "Settings",
      universe: "Live Universe",
      activity: "Runtime Activity",
    },
    labels: {
      network: "Network",
      language: "Language",
      accountAddress: "Account address",
      secretKey: "Secret key",
      apiUrl: "API URL",
      wsUrl: "WebSocket URL",
      maxExposure: "Maximum exposure",
      maxPositions: "Maximum concurrent positions",
      drawdown: "Daily drawdown stop",
      minRisk: "Min risk per trade",
      maxRisk: "Max risk per trade",
      maxSpread: "Max spread bps",
      topMarkets: "Top markets",
      refresh: "Refresh seconds",
      cooldown: "Execution cooldown",
      atrMin: "ATR stop min",
      atrMax: "ATR stop max",
      shadowMode: "Shadow mode",
      reduceOnly: "Reduce-only mode",
      realTradeStream: "Use real trade stream",
      externalSentiment: "Use external long/short data",
      minLiquidity: "Minimum liquidity score",
      minSignal: "Minimum signal strength",
      aggressiveSignal: "Aggressive signal strength",
      trendAlignment: "Require trend alignment",
      crossAlignment: "Require cross-exchange alignment",
      telegramEnabled: "Enable Telegram notifications",
      botToken: "Bot token",
      chatId: "Chat ID",
      summaryInterval: "Summary interval minutes",
      notifyApi: "Notify API status",
      notifyActions: "Notify engine actions",
      notifyTrades: "Notify trade activity",
      notifyPnl: "Notify PnL summary",
      notifyErrors: "Notify runtime errors",
    },
    table: {
      symbol: "Symbol",
      funding: "Funding",
      predicted: "Predicted",
      oi: "OI delta",
      crowd: "L/S",
      cvd: "CVD delta",
      signal: "Signal",
      strength: "Strength",
      side: "Side",
      size: "Size",
      notional: "Notional",
      entry: "Entry",
      mark: "Mark",
      pnl: "PnL",
      leverage: "Leverage",
      type: "Type",
      price: "Price",
      remaining: "Remaining",
      fee: "Fee",
      direction: "Direction",
      status: "Status",
      time: "Time",
      rank: "Rank",
      volume24h: "24h Volume",
      openInterest: "Open Interest",
      spread: "Spread",
    },
    emptySignals: "No qualified trades right now. The engine is watching the live top-liquidity universe.",
    emptyPositions: "No live positions found for this account.",
    emptyOrders: "No open orders found for this account.",
    emptyFills: "No recent fills found for this account.",
    emptyActivity: "No runtime activity yet.",
    emptyUniverse: "No live pairs loaded yet.",
    shadowExplained: "Simulate entries without sending live orders.",
    reduceExplained: "Allow only orders that reduce existing exposure.",
    runtimeStatus: "Runtime status",
    telegramStatus: "Telegram",
    liveAccount: "Live account",
  },
  id: {
    title: "Hyperliquid Trading Console",
    subtitle:
      "Funding, positioning, arus trade real, alignment lintas exchange, risk dinamis, dan notifikasi Telegram.",
    apiOnline: "API online",
    apiOffline: "API offline",
    migrationOk: "Migrasi ok",
    migrationPending: "Migrasi pending",
    topUniverse: "Top 50 pair paling liquid",
    executionShadow: "Eksekusi shadow",
    executionLive: "Eksekusi live",
    reduceOnlyOn: "Reduce-only aktif",
    reduceOnlyOff: "Reduce-only nonaktif",
    cancelAll: "Cancel semua",
    flattenAll: "Flatten semua",
    saveSettings: "Simpan pengaturan",
    saving: "Menyimpan",
    sendTelegramTest: "Kirim tes Telegram",
    sending: "Mengirim",
    refreshNow: "Refresh sekarang",
    nav: {
      dashboard: "Dashboard",
      pairs: "Pairs",
      settings: "Pengaturan",
    },
    metrics: {
      equity: "Equity",
      exposure: "Eksposur",
      withdrawable: "Saldo dapat ditarik",
      dailyPnl: "PnL harian",
      signals: "Sinyal",
      livePositions: "Posisi live",
    },
    sections: {
      signals: "Papan Sinyal Funding",
      positions: "Posisi Live",
      openOrders: "Open Order",
      fills: "Fill Terbaru",
      controls: "Kill Switch & Runtime",
      settings: "Pengaturan",
      universe: "Universe Live",
      activity: "Aktivitas Runtime",
    },
    labels: {
      network: "Network",
      language: "Bahasa",
      accountAddress: "Alamat akun",
      secretKey: "Secret key",
      apiUrl: "URL API",
      wsUrl: "URL WebSocket",
      maxExposure: "Eksposur maksimum",
      maxPositions: "Maksimum posisi bersamaan",
      drawdown: "Batas drawdown harian",
      minRisk: "Risk minimum per trade",
      maxRisk: "Risk maksimum per trade",
      maxSpread: "Spread maksimum bps",
      topMarkets: "Jumlah market",
      refresh: "Refresh detik",
      cooldown: "Cooldown eksekusi",
      atrMin: "ATR stop minimum",
      atrMax: "ATR stop maksimum",
      shadowMode: "Mode shadow",
      reduceOnly: "Mode reduce-only",
      realTradeStream: "Pakai trade stream real",
      externalSentiment: "Pakai data long/short eksternal",
      minLiquidity: "Skor likuiditas minimum",
      minSignal: "Kekuatan sinyal minimum",
      aggressiveSignal: "Sinyal ukuran agresif",
      trendAlignment: "Wajib align dengan trend",
      crossAlignment: "Wajib align lintas exchange",
      telegramEnabled: "Aktifkan notifikasi Telegram",
      botToken: "Bot token",
      chatId: "Chat ID",
      summaryInterval: "Interval ringkasan menit",
      notifyApi: "Kirim status API",
      notifyActions: "Kirim aksi engine",
      notifyTrades: "Kirim aktivitas trading",
      notifyPnl: "Kirim ringkasan PnL",
      notifyErrors: "Kirim error runtime",
    },
    table: {
      symbol: "Simbol",
      funding: "Funding",
      predicted: "Prediksi",
      oi: "Delta OI",
      crowd: "L/S",
      cvd: "Delta CVD",
      signal: "Sinyal",
      strength: "Kekuatan",
      side: "Sisi",
      size: "Ukuran",
      notional: "Notional",
      entry: "Entry",
      mark: "Mark",
      pnl: "PnL",
      leverage: "Leverage",
      type: "Tipe",
      price: "Harga",
      remaining: "Sisa",
      fee: "Fee",
      direction: "Arah",
      status: "Status",
      time: "Waktu",
      rank: "Rank",
      volume24h: "Volume 24j",
      openInterest: "Open Interest",
      spread: "Spread",
    },
    emptySignals: "Belum ada trade yang lolos filter. Engine tetap memantau universe live paling liquid.",
    emptyPositions: "Tidak ada posisi live untuk akun ini.",
    emptyOrders: "Tidak ada open order untuk akun ini.",
    emptyFills: "Belum ada fill terbaru untuk akun ini.",
    emptyActivity: "Belum ada aktivitas runtime.",
    emptyUniverse: "Pair live belum dimuat.",
    shadowExplained: "Simulasikan entry tanpa mengirim order live.",
    reduceExplained: "Hanya izinkan order yang mengurangi eksposur.",
    runtimeStatus: "Status runtime",
    telegramStatus: "Telegram",
    liveAccount: "Akun live",
  },
};

function classNames(...items) {
  return items.filter(Boolean).join(" ");
}

function formatUsd(value, digits = 0) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: digits,
  }).format(Number(value ?? 0));
}

function formatPct(value, digits = 2) {
  return `${(Number(value ?? 0) * 100).toFixed(digits)}%`;
}

function formatTs(value) {
  if (!value) return "-";
  return new Date(Number(value)).toLocaleString();
}

function Panel({ title, description, actions, children, className = "" }) {
  return (
    <section className={classNames("overflow-hidden rounded-2xl border border-white/10 bg-[#111827]/80", className)}>
      <div className="flex items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold tracking-wide text-white">{title}</h2>
          {description ? <p className="mt-1 text-xs text-slate-400">{description}</p> : null}
        </div>
        {actions}
      </div>
      <div>{children}</div>
    </section>
  );
}

function MetricCard({ label, value, detail, accent = "cyan" }) {
  const accents = {
    cyan: "from-cyan-400/20 to-cyan-400/5 text-cyan-100",
    emerald: "from-emerald-400/20 to-emerald-400/5 text-emerald-100",
    amber: "from-amber-300/20 to-amber-300/5 text-amber-100",
    rose: "from-rose-400/20 to-rose-400/5 text-rose-100",
  };
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/80 p-4">
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <div className={classNames("mt-3 rounded-xl bg-gradient-to-r px-3 py-4 text-2xl font-semibold", accents[accent])}>
        {value}
      </div>
      <p className="mt-3 text-sm text-slate-400">{detail}</p>
    </div>
  );
}

function Input({ label, value, onChange, type = "text", step, placeholder = "" }) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs uppercase tracking-[0.14em] text-slate-500">{label}</span>
      <input
        className="w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 outline-none placeholder:text-slate-600 focus:border-cyan-300/40"
        value={value}
        onChange={onChange}
        type={type}
        step={step}
        placeholder={placeholder}
      />
    </label>
  );
}

function Select({ label, value, onChange, options }) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs uppercase tracking-[0.14em] text-slate-500">{label}</span>
      <select
        className="w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 outline-none focus:border-cyan-300/40"
        value={value}
        onChange={onChange}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function Toggle({ label, checked, onChange, detail }) {
  return (
    <div className="rounded-xl border border-white/10 bg-slate-950 px-3 py-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-slate-200">{label}</p>
          {detail ? <p className="mt-1 text-xs text-slate-500">{detail}</p> : null}
        </div>
        <button
          type="button"
          onClick={onChange}
          className={classNames("relative h-6 w-11 rounded-full transition-colors", checked ? "bg-cyan-300" : "bg-slate-700")}
        >
          <span
            className={classNames(
              "absolute top-1 h-4 w-4 rounded-full bg-slate-950 transition-transform",
              checked ? "translate-x-6" : "translate-x-1",
            )}
          />
        </button>
      </div>
    </div>
  );
}

function StatusChip({ label, tone = "slate" }) {
  const tones = {
    slate: "border-white/10 bg-white/5 text-slate-300",
    cyan: "border-cyan-300/20 bg-cyan-300/10 text-cyan-100",
    emerald: "border-emerald-300/20 bg-emerald-300/10 text-emerald-100",
    amber: "border-amber-300/20 bg-amber-300/10 text-amber-100",
    rose: "border-rose-300/20 bg-rose-300/10 text-rose-100",
  };
  return <span className={classNames("rounded-full border px-3 py-1 text-xs font-medium", tones[tone])}>{label}</span>;
}

function MenuButton({ active, children, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={classNames(
        "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
        active ? "bg-cyan-300 text-slate-950" : "text-slate-300 hover:bg-white/10 hover:text-white",
      )}
    >
      {children}
    </button>
  );
}

function StrengthCell({ value }) {
  const pct = Math.round(Number(value ?? 0) * 100);
  const tone = pct >= 90 ? "bg-emerald-300" : pct >= 78 ? "bg-cyan-300" : "bg-slate-500";
  return (
    <div className="flex min-w-32 items-center gap-3">
      <div className="h-2 w-24 rounded-full bg-slate-800">
        <div className={classNames("h-2 rounded-full", tone)} style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-xs text-slate-300">{pct}</span>
    </div>
  );
}

function TableWrap({ children }) {
  return <div className="overflow-x-auto">{children}</div>;
}

function App() {
  const [activeMenu, setActiveMenu] = useState("dashboard");
  const [health, setHealth] = useState("checking");
  const [settingsPending, setSettingsPending] = useState(false);
  const [telegramTestPending, setTelegramTestPending] = useState(false);
  const [killPending, setKillPending] = useState("");
  const [flashMessage, setFlashMessage] = useState("");
  const [overview, setOverview] = useState({
    metrics: {},
    signals: [],
    orders: [],
    universe: [],
    positions: [],
    open_orders: [],
    fills: [],
    activity: [],
    last_error: null,
    migration_ok: false,
    migration_error: null,
    settings: {
      app: { language: "en" },
      hyperliquid: {},
      telegram: {},
      trading: {},
    },
  });
  const [settingsDraft, setSettingsDraft] = useState({
    app: { language: "en" },
    hyperliquid: {
      network: "mainnet",
      account_address: "",
      secret_key: "",
      api_url: "https://api.hyperliquid.xyz",
      ws_url: "wss://api.hyperliquid.xyz/ws",
      has_secret_key: false,
    },
    telegram: {
      enabled: false,
      bot_token: "",
      chat_id: "",
      has_bot_token: false,
      notify_api_status: true,
      notify_engine_actions: true,
      notify_trade_activity: true,
      notify_pnl_summary: true,
      notify_errors: true,
      summary_interval_minutes: 60,
    },
    trading: {
      max_total_exposure_pct: 0.3,
      max_concurrent_positions: 6,
      daily_drawdown_stop_pct: 0.03,
      min_risk_pct: 0.0025,
      max_risk_pct: 0.0075,
      max_spread_bps: 5,
      top_n_markets: 50,
      refresh_seconds: 60,
      execution_cooldown_seconds: 300,
      shadow_mode: true,
      reduce_only_mode: false,
      atr_stop_min: 1.2,
      atr_stop_max: 2,
      use_real_trade_stream: true,
      use_external_sentiment: true,
      min_liquidity_score: 0.15,
      min_signal_strength: 0.78,
      aggressive_signal_strength: 0.9,
      require_trend_alignment: true,
      require_cross_exchange_alignment: true,
    },
  });

  const language = settingsDraft.app?.language ?? "en";
  const t = copy[language] ?? copy.en;

  async function load() {
    try {
      const [healthRes, overviewRes] = await Promise.all([fetch(`${API_URL}/health`), fetch(`${API_URL}/dashboard/overview`)]);
      if (!healthRes.ok || !overviewRes.ok) throw new Error("bad response");
      const overviewPayload = await overviewRes.json();
      setHealth("online");
      setOverview(overviewPayload);
      setSettingsDraft(overviewPayload.settings);
    } catch {
      setHealth("offline");
    }
  }

  useEffect(() => {
    let cancelled = false;
    const runner = async () => {
      if (cancelled) return;
      await load();
    };
    runner();
    const intervalId = window.setInterval(runner, 15000);
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  const exposureUsd = useMemo(() => {
    return Number(overview.metrics.current_exposure_pct ?? 0) * Number(overview.metrics.equity_usd ?? 0);
  }, [overview.metrics]);

  function updateField(section, field, value) {
    setSettingsDraft((current) => ({
      ...current,
      [section]: {
        ...current[section],
        [field]: value,
      },
    }));
  }

  async function saveSettings() {
    setSettingsPending(true);
    try {
      const response = await fetch(`${API_URL}/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settingsDraft),
      });
      if (!response.ok) throw new Error("settings update failed");
      await load();
      setFlashMessage(language === "id" ? "Pengaturan tersimpan." : "Settings saved.");
    } catch {
      setHealth("offline");
      setFlashMessage(language === "id" ? "Gagal menyimpan pengaturan." : "Failed to save settings.");
    } finally {
      setSettingsPending(false);
    }
  }

  async function triggerKillSwitch(endpoint) {
    setKillPending(endpoint);
    try {
      const response = await fetch(`${API_URL}${endpoint}`, { method: "POST" });
      const payload = await response.json();
      await load();
      setFlashMessage(payload.message ?? "Done.");
    } catch {
      setHealth("offline");
      setFlashMessage(language === "id" ? "Aksi gagal dijalankan." : "Action failed.");
    } finally {
      setKillPending("");
    }
  }

  async function sendTelegramTest() {
    setTelegramTestPending(true);
    try {
      await fetch(`${API_URL}/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settingsDraft),
      });
      const response = await fetch(`${API_URL}/settings/telegram/test`, { method: "POST" });
      const payload = await response.json();
      await load();
      setFlashMessage(
        payload.sent
          ? language === "id"
            ? "Tes Telegram terkirim."
            : "Telegram test sent."
          : language === "id"
            ? "Tes Telegram tidak terkirim. Cek konfigurasi bot."
            : "Telegram test not sent. Check bot settings.",
      );
    } catch {
      setHealth("offline");
      setFlashMessage(language === "id" ? "Tes Telegram gagal." : "Telegram test failed.");
    } finally {
      setTelegramTestPending(false);
    }
  }

  const statusTone = health === "online" ? "emerald" : health === "checking" ? "amber" : "rose";

  return (
    <main className="min-h-screen bg-[#020617] text-slate-100">
      <div className="border-b border-white/10 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-semibold text-white">{t.title}</h1>
                <StatusChip label={health === "online" ? t.apiOnline : health === "offline" ? t.apiOffline : "Checking"} tone={statusTone} />
                <StatusChip
                  label={overview.migration_ok ? t.migrationOk : t.migrationPending}
                  tone={overview.migration_ok ? "cyan" : "amber"}
                />
                <StatusChip label={overview.metrics.network ?? settingsDraft.hyperliquid.network} tone="slate" />
                <StatusChip label={settingsDraft.trading.shadow_mode ? t.executionShadow : t.executionLive} tone="slate" />
                <StatusChip label={t.topUniverse} tone="slate" />
              </div>
              <p className="mt-2 max-w-3xl text-sm text-slate-400">{t.subtitle}</p>
              {overview.last_error ? <p className="mt-2 text-sm text-rose-300">Runtime error: {overview.last_error}</p> : null}
              {overview.migration_error ? <p className="mt-1 text-sm text-amber-300">Migration: {overview.migration_error}</p> : null}
              {flashMessage ? <p className="mt-2 text-sm text-cyan-200">{flashMessage}</p> : null}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => updateField("trading", "reduce_only_mode", !settingsDraft.trading.reduce_only_mode)}
                className="rounded-xl border border-white/10 bg-slate-900 px-4 py-2 text-sm text-slate-200 hover:bg-slate-800"
              >
                {settingsDraft.trading.reduce_only_mode ? t.reduceOnlyOn : t.reduceOnlyOff}
              </button>
              <button
                type="button"
                onClick={() => triggerKillSwitch("/engine/cancel-all")}
                disabled={killPending === "/engine/cancel-all"}
                className="rounded-xl bg-amber-300 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-amber-200 disabled:opacity-70"
              >
                {killPending === "/engine/cancel-all" ? "..." : t.cancelAll}
              </button>
              <button
                type="button"
                onClick={() => triggerKillSwitch("/engine/flatten-all")}
                disabled={killPending === "/engine/flatten-all"}
                className="rounded-xl bg-rose-300 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-rose-200 disabled:opacity-70"
              >
                {killPending === "/engine/flatten-all" ? "..." : t.flattenAll}
              </button>
              <button
                type="button"
                onClick={() => fetch(`${API_URL}/engine/refresh`, { method: "POST" }).then(load)}
                className="rounded-xl border border-cyan-300/30 bg-cyan-300/10 px-4 py-2 text-sm font-semibold text-cyan-100 hover:bg-cyan-300/20"
              >
                {t.refreshNow}
              </button>
            </div>
          </div>
          <nav className="mt-5 flex flex-wrap gap-2 border-t border-white/10 pt-4">
            <MenuButton active={activeMenu === "dashboard"} onClick={() => setActiveMenu("dashboard")}>
              {t.nav.dashboard}
            </MenuButton>
            <MenuButton active={activeMenu === "pairs"} onClick={() => setActiveMenu("pairs")}>
              {t.nav.pairs} ({overview.universe.length || settingsDraft.trading.top_n_markets || 50})
            </MenuButton>
            <MenuButton active={activeMenu === "settings"} onClick={() => setActiveMenu("settings")}>
              {t.nav.settings}
            </MenuButton>
          </nav>
        </div>
      </div>

      <div className="mx-auto grid max-w-7xl gap-5 px-4 py-6 sm:px-6 lg:grid-cols-12">
        {activeMenu === "dashboard" ? (
          <>
        <section className="grid gap-4 lg:col-span-12 lg:grid-cols-6">
          <MetricCard label={t.metrics.equity} value={formatUsd(overview.metrics.equity_usd)} detail={t.liveAccount} accent="cyan" />
          <MetricCard label={t.metrics.exposure} value={formatUsd(exposureUsd)} detail={formatPct(overview.metrics.current_exposure_pct)} accent="amber" />
          <MetricCard
            label={t.metrics.withdrawable}
            value={formatUsd(overview.metrics.withdrawable_usd)}
            detail={`${formatPct(overview.metrics.max_exposure_pct)} cap`}
            accent="emerald"
          />
          <MetricCard
            label={t.metrics.dailyPnl}
            value={formatUsd(overview.metrics.daily_pnl_usd, 2)}
            detail={`${formatPct(overview.metrics.daily_drawdown_stop_pct)} stop`}
            accent={Number(overview.metrics.daily_pnl_usd ?? 0) >= 0 ? "emerald" : "rose"}
          />
          <MetricCard label={t.metrics.signals} value={String(overview.metrics.signals_count ?? 0)} detail={t.runtimeStatus} accent="cyan" />
          <MetricCard
            label={t.metrics.livePositions}
            value={String(overview.metrics.positions_count ?? 0)}
            detail={`${overview.metrics.open_orders_count ?? 0} open orders`}
            accent="amber"
          />
        </section>

        <Panel title={t.sections.signals} className="lg:col-span-8" description="Thresholds 0.78 / 0.90">
          <TableWrap>
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.14em] text-slate-500">
                <tr>
                  {[t.table.symbol, t.table.funding, t.table.predicted, t.table.oi, t.table.crowd, t.table.cvd, t.table.signal, t.table.strength].map((head) => (
                    <th className="px-4 py-3 font-medium" key={head}>
                      {head}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {overview.signals.length ? (
                  overview.signals.map((row) => (
                    <tr key={row.symbol} className="hover:bg-white/[0.03]">
                      <td className="px-4 py-4 font-semibold text-white">{row.symbol}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatPct(row.funding, 3)}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatPct(row.predicted_funding, 3)}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatPct(row.oi_delta)}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatPct(row.long_short_ratio)}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatUsd(row.cvd_delta, 0)}</td>
                      <td className="px-4 py-4">
                        <span
                          className={classNames(
                            "rounded-lg px-2 py-1 text-xs font-semibold",
                            row.side === "long" ? "bg-emerald-400/10 text-emerald-200" : "bg-rose-400/10 text-rose-200",
                          )}
                        >
                          {`${row.strategy} ${row.side}`.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <StrengthCell value={row.strength} />
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td className="px-4 py-6 text-sm text-slate-500" colSpan={8}>
                      {t.emptySignals}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </TableWrap>
        </Panel>

        <Panel title={t.sections.controls} className="lg:col-span-4" description={t.telegramStatus}>
          <div className="space-y-4 p-5">
            <div className="grid gap-3">
              <Toggle
                label={t.labels.shadowMode}
                detail={t.shadowExplained}
                checked={Boolean(settingsDraft.trading.shadow_mode)}
                onChange={() => updateField("trading", "shadow_mode", !settingsDraft.trading.shadow_mode)}
              />
              <Toggle
                label={t.labels.reduceOnly}
                detail={t.reduceExplained}
                checked={Boolean(settingsDraft.trading.reduce_only_mode)}
                onChange={() => updateField("trading", "reduce_only_mode", !settingsDraft.trading.reduce_only_mode)}
              />
            </div>
            <div className="rounded-xl border border-white/10 bg-slate-950 p-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">{t.labels.network}</span>
                <span className="font-medium text-white">{overview.metrics.network ?? settingsDraft.hyperliquid.network}</span>
              </div>
              <div className="mt-3 flex items-center justify-between text-sm">
                <span className="text-slate-400">{t.metrics.livePositions}</span>
                <span className="font-medium text-white">{overview.metrics.positions_count ?? 0}</span>
              </div>
              <div className="mt-3 flex items-center justify-between text-sm">
                <span className="text-slate-400">{t.sections.openOrders}</span>
                <span className="font-medium text-white">{overview.metrics.open_orders_count ?? 0}</span>
              </div>
              <div className="mt-3 flex items-center justify-between text-sm">
                <span className="text-slate-400">{t.metrics.signals}</span>
                <span className="font-medium text-white">{overview.metrics.signals_count ?? 0}</span>
              </div>
            </div>
          </div>
        </Panel>

        <Panel title={t.sections.positions} className="lg:col-span-6">
          <TableWrap>
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.14em] text-slate-500">
                <tr>
                  {[t.table.symbol, t.table.side, t.table.size, t.table.notional, t.table.entry, t.table.mark, t.table.pnl, t.table.leverage].map((head) => (
                    <th className="px-4 py-3 font-medium" key={head}>
                      {head}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {overview.positions.length ? (
                  overview.positions.map((row) => (
                    <tr key={`${row.symbol}-${row.side}`} className="hover:bg-white/[0.03]">
                      <td className="px-4 py-4 font-semibold text-white">{row.symbol}</td>
                      <td className="px-4 py-4 capitalize text-slate-300">{row.side}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{Number(row.size ?? 0).toFixed(4)}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatUsd(row.notional_usd)}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatUsd(row.entry_price, 2)}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatUsd(row.mark_price, 2)}</td>
                      <td className={classNames("px-4 py-4 font-mono", Number(row.unrealized_pnl ?? 0) >= 0 ? "text-emerald-200" : "text-rose-200")}>
                        {formatUsd(row.unrealized_pnl, 2)}
                      </td>
                      <td className="px-4 py-4 font-mono text-slate-300">{Number(row.leverage ?? 0).toFixed(1)}x</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td className="px-4 py-6 text-sm text-slate-500" colSpan={8}>
                      {t.emptyPositions}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </TableWrap>
        </Panel>

        <Panel title={t.sections.openOrders} className="lg:col-span-6">
          <TableWrap>
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.14em] text-slate-500">
                <tr>
                  {[t.table.symbol, t.table.side, t.table.type, t.table.price, t.table.size, t.table.remaining, t.table.status, t.table.time].map((head) => (
                    <th className="px-4 py-3 font-medium" key={head}>
                      {head}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {overview.open_orders.length ? (
                  overview.open_orders.map((row) => (
                    <tr key={row.oid} className="hover:bg-white/[0.03]">
                      <td className="px-4 py-4 font-semibold text-white">{row.symbol}</td>
                      <td className="px-4 py-4 capitalize text-slate-300">{row.side}</td>
                      <td className="px-4 py-4 text-slate-300">{row.order_type}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatUsd(row.limit_price, 2)}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{Number(row.size ?? 0).toFixed(4)}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{Number(row.remaining_size ?? 0).toFixed(4)}</td>
                      <td className="px-4 py-4 text-slate-300">{row.status}</td>
                      <td className="px-4 py-4 text-slate-400">{formatTs(row.timestamp_ms)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td className="px-4 py-6 text-sm text-slate-500" colSpan={8}>
                      {t.emptyOrders}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </TableWrap>
        </Panel>

        <Panel title={t.sections.fills} className="lg:col-span-8">
          <TableWrap>
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.14em] text-slate-500">
                <tr>
                  {[t.table.symbol, t.table.side, t.table.direction, t.table.price, t.table.size, t.table.pnl, t.table.fee, t.table.time].map((head) => (
                    <th className="px-4 py-3 font-medium" key={head}>
                      {head}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {overview.fills.length ? (
                  overview.fills.map((row, index) => (
                    <tr key={`${row.symbol}-${row.timestamp_ms}-${index}`} className="hover:bg-white/[0.03]">
                      <td className="px-4 py-4 font-semibold text-white">{row.symbol}</td>
                      <td className="px-4 py-4 capitalize text-slate-300">{row.side}</td>
                      <td className="px-4 py-4 text-slate-300">{row.direction}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatUsd(row.price, 2)}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{Number(row.size ?? 0).toFixed(4)}</td>
                      <td className={classNames("px-4 py-4 font-mono", Number(row.closed_pnl ?? 0) >= 0 ? "text-emerald-200" : "text-rose-200")}>
                        {formatUsd(row.closed_pnl, 2)}
                      </td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatUsd(row.fee, 4)}</td>
                      <td className="px-4 py-4 text-slate-400">{formatTs(row.timestamp_ms)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td className="px-4 py-6 text-sm text-slate-500" colSpan={8}>
                      {t.emptyFills}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </TableWrap>
        </Panel>

        <Panel title={t.sections.activity} className="lg:col-span-4">
          <div className="space-y-2 p-5">
            {overview.activity.length ? (
              overview.activity.map((row, index) => (
                <div key={`${row}-${index}`} className="rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-slate-300">
                  {row}
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500">{t.emptyActivity}</p>
            )}
          </div>
        </Panel>
          </>
        ) : null}

        {activeMenu === "settings" ? (
        <Panel
          title={t.sections.settings}
          className="lg:col-span-12"
          actions={
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={sendTelegramTest}
                disabled={telegramTestPending}
                className="rounded-xl bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-200 disabled:opacity-70"
              >
                {telegramTestPending ? t.sending : t.sendTelegramTest}
              </button>
              <button
                type="button"
                onClick={saveSettings}
                disabled={settingsPending}
                className="rounded-xl bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-200 disabled:opacity-70"
              >
                {settingsPending ? t.saving : t.saveSettings}
              </button>
            </div>
          }
        >
          <div className="grid gap-5 p-5 lg:grid-cols-4">
            <div className="space-y-4">
              <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-400">App</h3>
              <Select
                label={t.labels.language}
                value={settingsDraft.app.language ?? "en"}
                onChange={(event) => updateField("app", "language", event.target.value)}
                options={[
                  { label: "English", value: "en" },
                  { label: "Indonesia", value: "id" },
                ]}
              />
              <Select
                label={t.labels.network}
                value={settingsDraft.hyperliquid.network ?? "mainnet"}
                onChange={(event) => updateField("hyperliquid", "network", event.target.value)}
                options={[
                  { label: "Mainnet", value: "mainnet" },
                  { label: "Testnet", value: "testnet" },
                ]}
              />
              <Input
                label={t.labels.accountAddress}
                value={settingsDraft.hyperliquid.account_address ?? ""}
                onChange={(event) => updateField("hyperliquid", "account_address", event.target.value)}
                placeholder="0x..."
              />
              <Input
                label={t.labels.secretKey}
                value={settingsDraft.hyperliquid.secret_key ?? ""}
                onChange={(event) => updateField("hyperliquid", "secret_key", event.target.value)}
                placeholder={settingsDraft.hyperliquid.has_secret_key ? "Stored secret retained if left blank" : "Enter secret key"}
              />
              <Input
                label={t.labels.apiUrl}
                value={settingsDraft.hyperliquid.api_url ?? ""}
                onChange={(event) => updateField("hyperliquid", "api_url", event.target.value)}
              />
              <Input
                label={t.labels.wsUrl}
                value={settingsDraft.hyperliquid.ws_url ?? ""}
                onChange={(event) => updateField("hyperliquid", "ws_url", event.target.value)}
              />
            </div>

            <div className="space-y-4">
              <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-400">Risk</h3>
              <div className="grid gap-4">
                <Input label={t.labels.maxExposure} type="number" step="0.01" value={settingsDraft.trading.max_total_exposure_pct ?? 0} onChange={(event) => updateField("trading", "max_total_exposure_pct", Number(event.target.value))} />
                <Input label={t.labels.maxPositions} type="number" step="1" value={settingsDraft.trading.max_concurrent_positions ?? 0} onChange={(event) => updateField("trading", "max_concurrent_positions", Number(event.target.value))} />
                <Input label={t.labels.drawdown} type="number" step="0.001" value={settingsDraft.trading.daily_drawdown_stop_pct ?? 0} onChange={(event) => updateField("trading", "daily_drawdown_stop_pct", Number(event.target.value))} />
                <Input label={t.labels.minRisk} type="number" step="0.0005" value={settingsDraft.trading.min_risk_pct ?? 0} onChange={(event) => updateField("trading", "min_risk_pct", Number(event.target.value))} />
                <Input label={t.labels.maxRisk} type="number" step="0.0005" value={settingsDraft.trading.max_risk_pct ?? 0} onChange={(event) => updateField("trading", "max_risk_pct", Number(event.target.value))} />
                <Input label={t.labels.maxSpread} type="number" step="0.1" value={settingsDraft.trading.max_spread_bps ?? 0} onChange={(event) => updateField("trading", "max_spread_bps", Number(event.target.value))} />
                <Input label={t.labels.topMarkets} type="number" step="1" value={settingsDraft.trading.top_n_markets ?? 50} onChange={(event) => updateField("trading", "top_n_markets", Number(event.target.value))} />
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-400">Execution</h3>
              <div className="grid gap-4">
                <Input label={t.labels.refresh} type="number" step="1" value={settingsDraft.trading.refresh_seconds ?? 0} onChange={(event) => updateField("trading", "refresh_seconds", Number(event.target.value))} />
                <Input label={t.labels.cooldown} type="number" step="1" value={settingsDraft.trading.execution_cooldown_seconds ?? 0} onChange={(event) => updateField("trading", "execution_cooldown_seconds", Number(event.target.value))} />
                <Input label={t.labels.atrMin} type="number" step="0.1" value={settingsDraft.trading.atr_stop_min ?? 0} onChange={(event) => updateField("trading", "atr_stop_min", Number(event.target.value))} />
                <Input label={t.labels.atrMax} type="number" step="0.1" value={settingsDraft.trading.atr_stop_max ?? 0} onChange={(event) => updateField("trading", "atr_stop_max", Number(event.target.value))} />
                <Input label={t.labels.minLiquidity} type="number" step="0.01" value={settingsDraft.trading.min_liquidity_score ?? 0} onChange={(event) => updateField("trading", "min_liquidity_score", Number(event.target.value))} />
                <Input label={t.labels.minSignal} type="number" step="0.01" value={settingsDraft.trading.min_signal_strength ?? 0} onChange={(event) => updateField("trading", "min_signal_strength", Number(event.target.value))} />
                <Input label={t.labels.aggressiveSignal} type="number" step="0.01" value={settingsDraft.trading.aggressive_signal_strength ?? 0} onChange={(event) => updateField("trading", "aggressive_signal_strength", Number(event.target.value))} />
              </div>
              <div className="grid gap-3">
                <Toggle label={t.labels.shadowMode} checked={Boolean(settingsDraft.trading.shadow_mode)} onChange={() => updateField("trading", "shadow_mode", !settingsDraft.trading.shadow_mode)} detail={t.shadowExplained} />
                <Toggle label={t.labels.reduceOnly} checked={Boolean(settingsDraft.trading.reduce_only_mode)} onChange={() => updateField("trading", "reduce_only_mode", !settingsDraft.trading.reduce_only_mode)} detail={t.reduceExplained} />
                <Toggle label={t.labels.realTradeStream} checked={Boolean(settingsDraft.trading.use_real_trade_stream)} onChange={() => updateField("trading", "use_real_trade_stream", !settingsDraft.trading.use_real_trade_stream)} />
                <Toggle label={t.labels.externalSentiment} checked={Boolean(settingsDraft.trading.use_external_sentiment)} onChange={() => updateField("trading", "use_external_sentiment", !settingsDraft.trading.use_external_sentiment)} />
                <Toggle label={t.labels.trendAlignment} checked={Boolean(settingsDraft.trading.require_trend_alignment)} onChange={() => updateField("trading", "require_trend_alignment", !settingsDraft.trading.require_trend_alignment)} />
                <Toggle label={t.labels.crossAlignment} checked={Boolean(settingsDraft.trading.require_cross_exchange_alignment)} onChange={() => updateField("trading", "require_cross_exchange_alignment", !settingsDraft.trading.require_cross_exchange_alignment)} />
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-400">Telegram</h3>
              <Toggle
                label={t.labels.telegramEnabled}
                checked={Boolean(settingsDraft.telegram.enabled)}
                onChange={() => updateField("telegram", "enabled", !settingsDraft.telegram.enabled)}
              />
              <Input
                label={t.labels.botToken}
                value={settingsDraft.telegram.bot_token ?? ""}
                onChange={(event) => updateField("telegram", "bot_token", event.target.value)}
                placeholder={settingsDraft.telegram.has_bot_token ? "Stored token retained if left blank" : "123456:ABC..."}
              />
              <Input label={t.labels.chatId} value={settingsDraft.telegram.chat_id ?? ""} onChange={(event) => updateField("telegram", "chat_id", event.target.value)} />
              <Input
                label={t.labels.summaryInterval}
                type="number"
                step="1"
                value={settingsDraft.telegram.summary_interval_minutes ?? 60}
                onChange={(event) => updateField("telegram", "summary_interval_minutes", Number(event.target.value))}
              />
              <div className="grid gap-3">
                <Toggle label={t.labels.notifyApi} checked={Boolean(settingsDraft.telegram.notify_api_status)} onChange={() => updateField("telegram", "notify_api_status", !settingsDraft.telegram.notify_api_status)} />
                <Toggle label={t.labels.notifyActions} checked={Boolean(settingsDraft.telegram.notify_engine_actions)} onChange={() => updateField("telegram", "notify_engine_actions", !settingsDraft.telegram.notify_engine_actions)} />
                <Toggle label={t.labels.notifyTrades} checked={Boolean(settingsDraft.telegram.notify_trade_activity)} onChange={() => updateField("telegram", "notify_trade_activity", !settingsDraft.telegram.notify_trade_activity)} />
                <Toggle label={t.labels.notifyPnl} checked={Boolean(settingsDraft.telegram.notify_pnl_summary)} onChange={() => updateField("telegram", "notify_pnl_summary", !settingsDraft.telegram.notify_pnl_summary)} />
                <Toggle label={t.labels.notifyErrors} checked={Boolean(settingsDraft.telegram.notify_errors)} onChange={() => updateField("telegram", "notify_errors", !settingsDraft.telegram.notify_errors)} />
              </div>
            </div>
          </div>
        </Panel>
        ) : null}

        {activeMenu === "pairs" ? (
        <Panel title={t.sections.universe} description={t.topUniverse} className="lg:col-span-12">
          <TableWrap>
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.14em] text-slate-500">
                <tr>
                  {[t.table.rank, t.table.symbol, t.table.volume24h, t.table.openInterest, t.table.spread].map((head) => (
                    <th className="px-4 py-3 font-medium" key={head}>
                      {head}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {overview.universe.length ? (
                  overview.universe.map((row, index) => (
                    <tr key={row.symbol} className="hover:bg-white/[0.03]">
                      <td className="px-4 py-4 font-mono text-slate-400">#{index + 1}</td>
                      <td className="px-4 py-4 font-semibold text-white">{row.symbol}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatUsd(row.volume_24h)}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{formatUsd(row.open_interest_usd)}</td>
                      <td className="px-4 py-4 font-mono text-slate-300">{Number(row.spread_bps ?? 0).toFixed(2)} bps</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td className="px-4 py-6 text-sm text-slate-500" colSpan={5}>
                      {t.emptyUniverse}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </TableWrap>
        </Panel>
        ) : null}
      </div>
    </main>
  );
}

export default App;
