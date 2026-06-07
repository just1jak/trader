import React, { useEffect, useMemo, useState } from 'react';
import { useApi } from './hooks/useApi';
import './App.css';

type StrategyKey =
  | 'ma_crossover'
  | 'orb'
  | 'delta_scalp'
  | 'ema_scalp'
  | 'support_resistance_flip'
  | 'volume_profile_orderflow';

type BacktestForm = {
  symbol: string;
  from: string;
  to: string;
  timeframe: string;
  strategy: StrategyKey;
  params: Record<string, number | string | boolean>;
  source: 'sample' | 'tradovate';
};

type Metric = {
  label: string;
  value: string;
  detail?: string;
  tone?: 'positive' | 'negative' | 'neutral';
};

type Trade = {
  id: number;
  entryTime: string;
  exitTime: string;
  side: 'Long' | 'Short';
  entry: number;
  exit: number;
  quantity: number;
  pnlPoints: number;
  pnlDollars: number;
  rMultiple: number;
  reason: string;
};

type BacktestResults = {
  metrics: Metric[];
  trades: Trade[];
  equity: number[];
  buyHold: number[];
  completedAt: string;
  duration: string;
  dataSource: string;
  fees: string;
};

type ApiHealth = {
  status: string;
  mode: string;
  live_trading_enabled: boolean;
  sources: Record<string, boolean>;
  routes: Record<string, string>;
};

type DataPreview = {
  source: string;
  symbol: string;
  timeframe: string;
  rows: number;
};

type TradeFilter = 'all' | 'winners' | 'losers';

const strategyOptions: Array<{
  key: StrategyKey;
  label: string;
  summary: string;
  risk: string[];
  params: Array<{
    key: string;
    label: string;
    suffix?: string;
    type?: 'number' | 'select';
    options?: string[];
  }>;
}> = [
  {
    key: 'ma_crossover',
    label: 'MA Crossover',
    summary: 'Uses fast and slow moving averages to stay with broad directional momentum.',
    risk: ['Watch chop in range-bound sessions', 'Use wider stops for daily data', 'Confirm signal persistence'],
    params: [
      { key: 'fast', label: 'Fast MA' },
      { key: 'slow', label: 'Slow MA' },
    ],
  },
  {
    key: 'orb',
    label: 'Opening Range Breakout',
    summary: 'Breaks the high or low of the initial range with confirmation and trend-following exits.',
    risk: ['Uses prior range to avoid lookahead', 'ATR filter is fixed at 14 bars in backend', 'Review fills around session open'],
    params: [
      { key: 'orb_minutes', label: 'Opening range', suffix: 'min' },
      { key: 'breakout_mult', label: 'Breakout buffer', suffix: 'ATR' },
    ],
  },
  {
    key: 'delta_scalp',
    label: 'Delta Scalp',
    summary: 'Looks for order-flow imbalance where buying or selling pressure dominates recent bars.',
    risk: ['Requires reliable volume', 'Approximate delta when time-sales is unavailable', 'Avoid low-liquidity sessions'],
    params: [
      { key: 'delta_threshold', label: 'Delta threshold' },
      { key: 'delta_ma_period', label: 'Delta MA' },
    ],
  },
  {
    key: 'ema_scalp',
    label: 'Micro-Trend EMA Scalp',
    summary: 'Uses a very fast EMA pair with forced exits to test scalping-style trend bursts.',
    risk: ['Sensitive to spread and fees', 'Limit hold time', 'Review trade count inflation'],
    params: [
      { key: 'fast', label: 'Fast EMA' },
      { key: 'slow', label: 'Slow EMA' },
      { key: 'max_hold_bars', label: 'Max hold', suffix: 'bars' },
    ],
  },
  {
    key: 'support_resistance_flip',
    label: 'Support/Resistance Flip',
    summary: 'Waits for a level break and retest before entering in the new direction.',
    risk: ['Level detection can lag', 'Retest tolerance must match tick size', 'Reject weak volume retests'],
    params: [
      { key: 'lookback', label: 'Lookback' },
      { key: 'retest_tolerance', label: 'Retest tolerance', suffix: 'pts' },
    ],
  },
  {
    key: 'volume_profile_orderflow',
    label: 'Volume Profile Order Flow',
    summary: 'Combines value area, POC, low-volume nodes, and delta pressure to find higher-conviction zones.',
    risk: ['Best with time-sales data', 'Avoid look-ahead profile construction', 'Validate bin size by instrument'],
    params: [
      { key: 'lookback_period', label: 'Lookback' },
      { key: 'price_bin_size', label: 'Bin size', suffix: 'pts' },
      { key: 'volume_threshold', label: 'Volume threshold' },
      { key: 'delta_threshold', label: 'Delta threshold' },
      { key: 'lv_breakout_volume_mult', label: 'LVN volume mult' },
    ],
  },
];

const defaultParams: Record<StrategyKey, BacktestForm['params']> = {
  ma_crossover: { fast: 9, slow: 21 },
  orb: {
    orb_minutes: 30,
    breakout_mult: 0.25,
  },
  delta_scalp: { delta_threshold: 0.5, delta_ma_period: 10 },
  ema_scalp: { fast: 3, slow: 8, max_hold_bars: 5 },
  support_resistance_flip: { lookback: 20, retest_tolerance: 0.5 },
  volume_profile_orderflow: {
    lookback_period: 20,
    price_bin_size: 0.25,
    volume_threshold: 2,
    delta_threshold: 0.5,
    lv_breakout_volume_mult: 1.5,
  },
};

const sampleResults: BacktestResults = {
  metrics: [
    { label: 'Total Return', value: '+23.47%', detail: '+$11,735.00', tone: 'positive' },
    { label: 'Sharpe Ratio', value: '1.48', detail: 'Daily annualized', tone: 'neutral' },
    { label: 'Max Drawdown', value: '-8.32%', detail: '-$4,158.00', tone: 'negative' },
    { label: 'Win Rate', value: '58.33%', detail: '42 / 72 trades', tone: 'positive' },
    { label: 'Net Profit', value: '$11,735.00', detail: 'Profit factor 1.92', tone: 'positive' },
    { label: 'Total Trades', value: '72', detail: '4 max per day', tone: 'neutral' },
    { label: 'Avg Win', value: '$413.19', detail: '-$276.44 avg loss', tone: 'positive' },
  ],
  equity: [
    94000, 95800, 96450, 95750, 97000, 98200, 99600, 100100, 101800, 103400,
    102100, 102900, 101700, 103800, 104900, 105500, 106800, 105600, 104200,
    103600, 105200, 106400, 107900, 110100, 112300, 114900, 116200, 118700,
    121400, 123200, 122100, 124800, 126900, 124100, 121900, 120800, 123475,
  ],
  buyHold: [
    93500, 92500, 91200, 91900, 92800, 94400, 95200, 95800, 96500, 97100,
    98200, 98900, 99300, 100100, 100900, 101600, 102100, 103000, 103800,
    104400, 104000, 104900, 105400, 106800, 108200, 107600, 108900, 109500,
    110100, 109800, 110600, 109900, 110500, 109900, 110300, 109600, 109362,
  ],
  trades: [
    {
      id: 1,
      entryTime: '2024-05-31 09:45',
      exitTime: '2024-05-31 10:15',
      side: 'Long',
      entry: 5298,
      exit: 5308.25,
      quantity: 1,
      pnlPoints: 10.25,
      pnlDollars: 512.5,
      rMultiple: 1.71,
      reason: 'Profit target',
    },
    {
      id: 2,
      entryTime: '2024-05-31 11:00',
      exitTime: '2024-05-31 11:27',
      side: 'Short',
      entry: 5305.5,
      exit: 5300.5,
      quantity: 1,
      pnlPoints: 5,
      pnlDollars: 250,
      rMultiple: 0.83,
      reason: 'Trailing stop',
    },
    {
      id: 3,
      entryTime: '2024-05-31 13:15',
      exitTime: '2024-05-31 13:45',
      side: 'Long',
      entry: 5312.25,
      exit: 5304.25,
      quantity: 1,
      pnlPoints: -8,
      pnlDollars: -400,
      rMultiple: -1.33,
      reason: 'Stop loss',
    },
    {
      id: 4,
      entryTime: '2024-05-30 09:45',
      exitTime: '2024-05-30 10:30',
      side: 'Long',
      entry: 5285.75,
      exit: 5297.75,
      quantity: 1,
      pnlPoints: 12,
      pnlDollars: 600,
      rMultiple: 2,
      reason: 'Profit target',
    },
    {
      id: 5,
      entryTime: '2024-05-30 11:15',
      exitTime: '2024-05-30 11:42',
      side: 'Short',
      entry: 5291.25,
      exit: 5286.25,
      quantity: 1,
      pnlPoints: 5,
      pnlDollars: 250,
      rMultiple: 0.83,
      reason: 'Trailing stop',
    },
    {
      id: 6,
      entryTime: '2024-05-30 14:00',
      exitTime: '2024-05-30 14:22',
      side: 'Short',
      entry: 5286,
      exit: 5288.5,
      quantity: 1,
      pnlPoints: -2.5,
      pnlDollars: -125,
      rMultiple: -0.42,
      reason: 'Stop loss',
    },
  ],
  completedAt: '6/1/2024 10:24 AM',
  duration: '00:02:18',
  dataSource: 'Tradovate demo',
  fees: '$2.50 per side',
};

const navItems = [
  { label: 'Backtest', icon: <TrendIcon /> },
  { label: 'Strategies', icon: <GridIcon /> },
  { label: 'Results', icon: <ClockIcon /> },
  { label: 'Exports', icon: <DownloadIcon /> },
  { label: 'Notebook', icon: <DocumentIcon /> },
  { label: 'Settings', icon: <CogIcon /> },
];

function App() {
  const { callApi, loading, error, clearError } = useApi();
  const [activeNav, setActiveNav] = useState('Backtest');
  const [formData, setFormData] = useState<BacktestForm>({
    symbol: 'ES',
    from: '2025-01-02',
    to: '2025-01-02',
    timeframe: '1min',
    strategy: 'orb',
    params: defaultParams.orb,
    source: 'sample',
  });
  const [results, setResults] = useState<BacktestResults>(sampleResults);
  const [search, setSearch] = useState('');
  const [selectedTradeId, setSelectedTradeId] = useState(1);
  const [apiHealth, setApiHealth] = useState<ApiHealth | null>(null);
  const [backendStrategies, setBackendStrategies] = useState<Array<{ key: string; label: string }>>([]);
  const [dataPreview, setDataPreview] = useState<DataPreview | null>(null);
  const [chartRange, setChartRange] = useState('All');
  const [tradeFilter, setTradeFilter] = useState<TradeFilter>('all');
  const [lastAction, setLastAction] = useState('Waiting for first backend run');

  const selectedStrategy = useMemo(
    () => strategyOptions.find((strategy) => strategy.key === formData.strategy) ?? strategyOptions[0],
    [formData.strategy],
  );

  const filteredTrades = results.trades.filter((trade) => {
    const needle = search.trim().toLowerCase();
    const matchesSearch = !needle || `${trade.entryTime} ${trade.exitTime} ${trade.side} ${trade.reason}`.toLowerCase().includes(needle);
    const matchesFilter =
      tradeFilter === 'all' ||
      (tradeFilter === 'winners' && trade.pnlDollars >= 0) ||
      (tradeFilter === 'losers' && trade.pnlDollars < 0);
    return matchesSearch && matchesFilter;
  });

  useEffect(() => {
    const loadBackendStatus = async () => {
      const [health, strategies] = await Promise.all([
        callApi<ApiHealth>('/api/v1/health'),
        callApi<{ strategies: Array<{ key: string; label: string }> }>('/api/v1/strategies'),
      ]);
      if (health) setApiHealth(health);
      if (strategies?.strategies) setBackendStrategies(strategies.strategies);
    };

    loadBackendStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    refreshDataPreview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.symbol, formData.timeframe, formData.from, formData.to, formData.source]);

  const updateField = (field: keyof BacktestForm, value: string) => {
    if (field === 'strategy') {
      const strategy = value as StrategyKey;
      setFormData((previous) => ({
        ...previous,
        strategy,
        params: defaultParams[strategy],
      }));
      return;
    }
    if (field === 'source') {
      setFormData((previous) => ({
        ...previous,
        source: value as BacktestForm['source'],
      }));
      return;
    }

    setFormData((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const updateParam = (param: string, value: string) => {
    const parsed = value === '' ? '' : Number(value);
    setFormData((previous) => ({
      ...previous,
      params: {
        ...previous.params,
        [param]: Number.isNaN(parsed) ? value : parsed,
      },
    }));
  };

  const runBacktest = async () => {
    clearError();
    setLastAction('Requesting candles from backend...');
    await refreshDataPreview();
    setLastAction('Running backend backtest...');
    const data = await callApi<any>('/api/v1/backtest', {
      method: 'POST',
      body: JSON.stringify(formData),
    });

    if (data?.metrics) {
      setResults(normalizeApiResults(data));
      setLastAction(`Backtest completed from ${data.data_source ?? formData.source} data`);
    }
  };

  const refreshDataPreview = async () => {
    if (formData.source === 'tradovate' && !apiHealth?.sources?.tradovate) {
      setDataPreview(null);
      setLastAction('Tradovate credentials are not configured');
      return null;
    }

    const params = new URLSearchParams({
      symbol: formData.symbol,
      source: formData.source,
      timeframe: formData.timeframe,
      from: formData.from,
      to: formData.to,
    });
    const data = await callApi<DataPreview>(`/api/v1/market/backtest-data?${params.toString()}`);
    if (data) {
      setDataPreview(data);
      setLastAction(`Loaded ${data.rows} ${data.timeframe} candles from ${data.source}`);
    }
    return data;
  };

  const cycleTradeFilter = () => {
    setTradeFilter((current) => (current === 'all' ? 'winners' : current === 'winners' ? 'losers' : 'all'));
  };

  const exportTradesCsv = () => {
    const rows = [
      ['id', 'entryTime', 'exitTime', 'side', 'entry', 'exit', 'quantity', 'pnlPoints', 'pnlDollars', 'rMultiple', 'reason'],
      ...filteredTrades.map((trade) => [
        trade.id,
        trade.entryTime,
        trade.exitTime,
        trade.side,
        trade.entry,
        trade.exit,
        trade.quantity,
        trade.pnlPoints,
        trade.pnlDollars,
        trade.rMultiple,
        trade.reason,
      ]),
    ];
    const csv = rows.map((row) => row.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `forge-trades-${formData.symbol}-${formData.from}-to-${formData.to}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    setLastAction(`Exported ${filteredTrades.length} trades to CSV`);
  };

  return (
    <div className="app-shell">
      <aside className="side-rail" aria-label="Primary navigation">
        <div className="brand-mark">
          <ForgeIcon />
          <div>
            <strong>FORGE</strong>
            <span>LABS</span>
          </div>
        </div>

        <nav className="rail-nav">
          {navItems.map((item, index) => (
            <button
              className={`rail-button ${activeNav === item.label ? 'is-active' : ''}`}
              key={item.label}
              onClick={() => setActiveNav(item.label)}
              type="button"
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="rail-footer">
          <div className="rail-card">
            <span>Simulation mode</span>
            <p>All trades simulated. No live orders sent.</p>
            <button type="button">Review risk</button>
          </div>

          <div className="rail-status">
            <span className="status-dot" />
            <span>{apiHealth?.status === 'ok' ? 'Backend connected' : 'Backend pending'}</span>
          </div>
        </div>
      </aside>

      <main className="workspace">
        <header className="top-bar">
          <div className="page-title">
            <ChartIcon />
            <h1>{activeNav}</h1>
          </div>

          <div className="system-status" aria-label="System status">
            <span className="status-dot" />
            <strong>Simulation only</strong>
            <span className="muted-dot" />
            <span>{dataPreview ? `${dataPreview.rows} candles loaded` : lastAction}</span>
            <SunIcon />
          </div>
        </header>

        {activeNav !== 'Backtest' ? (
          <ModulePanel
            activeNav={activeNav}
            apiHealth={apiHealth}
            backendStrategies={backendStrategies}
            exportTradesCsv={exportTradesCsv}
            results={results}
          />
        ) : (
          <>
        <section className="config-panel" aria-label="Backtest configuration">
          <div className="config-grid">
            <Field label="Symbol" className="symbol-field">
              <select value={formData.symbol} onChange={(event) => updateField('symbol', event.target.value)}>
                <option value="ES">ES - E-mini S&P 500 Futures</option>
                <option value="NQ">NQ - E-mini Nasdaq 100</option>
                <option value="CL">CL - Crude Oil</option>
                <option value="GC">GC - Gold</option>
              </select>
            </Field>

            <Field label="Date range" className="date-field">
              <div className="date-range">
                <input type="date" value={formData.from} onChange={(event) => updateField('from', event.target.value)} />
                <span>to</span>
                <input type="date" value={formData.to} onChange={(event) => updateField('to', event.target.value)} />
              </div>
            </Field>

            <Field label="Timeframe">
              <select value={formData.timeframe} onChange={(event) => updateField('timeframe', event.target.value)}>
                <option value="1min">1m</option>
                <option value="5min">5m</option>
                <option value="15min">15m</option>
                <option value="1h">1h</option>
                <option value="1d">1d</option>
              </select>
            </Field>

            <Field label="Strategy" className="strategy-field">
              <select value={formData.strategy} onChange={(event) => updateField('strategy', event.target.value)}>
                {strategyOptions.map((strategy) => (
                  <option key={strategy.key} value={strategy.key}>
                    {strategy.label}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Data source">
              <select value={formData.source} onChange={(event) => updateField('source', event.target.value)}>
                <option value="sample">Sample CSV</option>
                <option value="tradovate">Tradovate</option>
              </select>
            </Field>

            <div className="command-stack">
              <button className="run-button" type="button" onClick={runBacktest} disabled={loading}>
                <PlayIcon />
                {loading ? 'Running...' : 'Run backtest'}
              </button>
              <button className="reset-button" type="button" onClick={() => setFormData({ ...formData, params: defaultParams[formData.strategy] })}>
                <ResetIcon />
                Reset
              </button>
            </div>
          </div>

          <div className="parameter-section">
            <div className="section-rule">
              <h2>Strategy parameters</h2>
              <ChevronUpIcon />
            </div>

            <div className="parameter-grid">
              {selectedStrategy.params.map((param) => (
                <Field label={param.label} key={param.key}>
                  <div className="input-with-suffix">
                    <input
                      type="number"
                      value={String(formData.params[param.key] ?? '')}
                      onChange={(event) => updateParam(param.key, event.target.value)}
                    />
                    {param.suffix && <span>{param.suffix}</span>}
                  </div>
                </Field>
              ))}

              <label className="checkbox-field">
                <input
                  type="checkbox"
                  checked={Boolean(formData.params.trade_outside_rth)}
                  onChange={(event) =>
                    setFormData((previous) => ({
                      ...previous,
                      params: {
                        ...previous.params,
                        trade_outside_rth: event.target.checked,
                      },
                    }))
                  }
                />
                <span>Trade outside RTH</span>
              </label>
            </div>
          </div>
        </section>

        {error && (
          <div className="error-banner" role="status">
            <strong>Backend unavailable.</strong>
            <span>{error}. Showing the last completed simulation.</span>
          </div>
        )}

        <section className="content-grid">
          <div className="main-column">
            <MetricStrip metrics={results.metrics} />
            <EquityPanel
              buyHold={results.buyHold}
              chartRange={chartRange}
              equity={results.equity}
              setChartRange={setChartRange}
            />
            <TradesPanel
              exportTradesCsv={exportTradesCsv}
              filteredTrades={filteredTrades}
              tradeFilter={tradeFilter}
              cycleTradeFilter={cycleTradeFilter}
              search={search}
              selectedTradeId={selectedTradeId}
              setSearch={setSearch}
              setSelectedTradeId={setSelectedTradeId}
              totalTrades={results.trades.length}
            />
          </div>

          <StrategyPanel
            completedAt={results.completedAt}
            dataSource={results.dataSource}
            duration={results.duration}
            fees={results.fees}
            formData={formData}
            strategy={selectedStrategy}
          />
        </section>
          </>
        )}
      </main>
    </div>
  );
}

function Field({ children, className = '', label }: { children: React.ReactNode; className?: string; label: string }) {
  return (
    <label className={`field ${className}`}>
      <span>{label}</span>
      {children}
    </label>
  );
}

function ModulePanel({
  activeNav,
  apiHealth,
  backendStrategies,
  exportTradesCsv,
  results,
}: {
  activeNav: string;
  apiHealth: ApiHealth | null;
  backendStrategies: Array<{ key: string; label: string }>;
  exportTradesCsv: () => void;
  results: BacktestResults;
}) {
  const routeEntries = apiHealth ? Object.entries(apiHealth.routes) : [];

  return (
    <section className="module-panel">
      <div className="module-hero">
        <div>
          <span>{activeNav}</span>
          <h2>{moduleTitle(activeNav)}</h2>
          <p>{moduleDescription(activeNav)}</p>
        </div>
        <strong className={apiHealth?.status === 'ok' ? 'module-status-ok' : 'module-status-warn'}>
          {apiHealth?.status === 'ok' ? 'API connected' : 'API not confirmed'}
        </strong>
      </div>

      <div className="module-grid">
        {activeNav === 'Strategies' && (
          <article className="module-card">
            <h3>Backend strategies</h3>
            <ul>
              {(backendStrategies.length ? backendStrategies : strategyOptions).map((strategy) => (
                <li key={strategy.key}>
                  <span>{strategy.label}</span>
                  <strong>{strategy.key}</strong>
                </li>
              ))}
            </ul>
          </article>
        )}

        {activeNav === 'Results' && (
          <article className="module-card">
            <h3>Last run summary</h3>
            <ul>
              {results.metrics.slice(0, 6).map((metric) => (
                <li key={metric.label}>
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                </li>
              ))}
            </ul>
          </article>
        )}

        {activeNav === 'Exports' && (
          <article className="module-card">
            <h3>Available export</h3>
            <p>Trade CSV export is wired to the current filtered trade table.</p>
            <button className="run-button" type="button" onClick={exportTradesCsv}>
              <DownloadIcon />
              Export trades
            </button>
          </article>
        )}

        <article className="module-card">
          <h3>API routes online</h3>
          <ul>
            {routeEntries.length ? (
              routeEntries.map(([name, route]) => (
                <li key={name}>
                  <span>{name.replace(/_/g, ' ')}</span>
                  <strong>{route}</strong>
                </li>
              ))
            ) : (
              <li>
                <span>Run backend</span>
                <strong>Waiting for /api/v1/health</strong>
              </li>
            )}
          </ul>
        </article>

        <article className="module-card">
          <h3>Build status</h3>
          <p>
            This module has honest app state now. Backtest, strategy metadata, route discovery,
            result summary, and trade export are wired; notebook/settings still need real persistence.
          </p>
        </article>
      </div>
    </section>
  );
}

function MetricStrip({ metrics }: { metrics: Metric[] }) {
  return (
    <section className="metric-strip" aria-label="Backtest metrics">
      {metrics.map((metric, index) => (
        <article className="metric-item" key={metric.label}>
          <div className="metric-label">
            <span>{metric.label}</span>
            <InfoIcon />
          </div>
          <strong className={metric.tone ? `tone-${metric.tone}` : ''}>{metric.value}</strong>
          {metric.detail && <small>{metric.detail}</small>}
          <span className={`metric-glyph metric-glyph-${index + 1}`} aria-hidden="true" />
        </article>
      ))}
    </section>
  );
}

function EquityPanel({
  buyHold,
  chartRange,
  equity,
  setChartRange,
}: {
  buyHold: number[];
  chartRange: string;
  equity: number[];
  setChartRange: (range: string) => void;
}) {
  const visibleEquity = sliceSeriesForRange(equity, chartRange);
  const visibleBuyHold = sliceSeriesForRange(buyHold, chartRange);
  const backtestPath = buildLinePath(visibleEquity, 1040, 260);
  const buyHoldPath = buildLinePath(visibleBuyHold, 1040, 260);
  const lastEquity = visibleEquity[visibleEquity.length - 1] ?? 0;
  const lastBuyHold = visibleBuyHold[visibleBuyHold.length - 1] ?? 0;

  return (
    <section className="chart-panel">
      <div className="panel-header">
        <div className="panel-title">
          <h2>Equity curve comparison</h2>
          <InfoIcon />
        </div>
        <div className="chart-actions" aria-label="Chart range controls">
          {['1M', '3M', '6M', 'YTD', '1Y', 'All'].map((range) => (
            <button className={range === chartRange ? 'is-active' : ''} key={range} onClick={() => setChartRange(range)} type="button">
              {range}
            </button>
          ))}
          <button className="icon-button" type="button" aria-label="Expand chart">
            <ExpandIcon />
          </button>
          <button className="icon-button" type="button" aria-label="Chart menu">
            <MenuIcon />
          </button>
        </div>
      </div>

      <div className="chart-legend">
        <span className="legend-item legend-backtest">Backtest</span>
        <span className="legend-item legend-buyhold">Buy & Hold</span>
        <span className="chart-note">In-sample strategy replay</span>
      </div>

      <div className="chart-frame">
        <div className="axis-labels">
          {['$130K', '$120K', '$110K', '$100K', '$90K', '$80K', '$70K'].map((label) => (
            <span key={label}>{label}</span>
          ))}
        </div>
        <svg className="equity-chart" viewBox="0 0 1040 260" role="img" aria-label="Backtest equity curve compared with buy and hold">
          <defs>
            <linearGradient id="equityFill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#37ff6b" stopOpacity="0.22" />
              <stop offset="100%" stopColor="#37ff6b" stopOpacity="0" />
            </linearGradient>
          </defs>
          {[0, 43, 87, 130, 173, 217, 260].map((y) => (
            <line className="grid-line" key={y} x1="0" x2="1040" y1={y} y2={y} />
          ))}
          <line className="baseline" x1="0" x2="1040" y1="150" y2="150" />
          <path className="area-fill" d={`${backtestPath} L 1040 260 L 0 260 Z`} />
          <path className="buyhold-line" d={buyHoldPath} />
          <path className="backtest-line" d={backtestPath} />
          <g transform="translate(1015 69)">
            <rect className="value-tag tag-backtest" height="24" rx="5" width="74" />
            <text x="9" y="16">${Math.round(lastEquity).toLocaleString()}</text>
          </g>
          <g transform="translate(1017 121)">
            <rect className="value-tag tag-buyhold" height="24" rx="5" width="72" />
            <text x="9" y="16">${Math.round(lastBuyHold).toLocaleString()}</text>
          </g>
        </svg>
        <div className="month-labels">
          {["Jan '24", "Feb '24", "Mar '24", "Apr '24", "May '24", "Jun '24"].map((label) => (
            <span key={label}>{label}</span>
          ))}
        </div>
      </div>
    </section>
  );
}

function TradesPanel({
  cycleTradeFilter,
  exportTradesCsv,
  filteredTrades,
  search,
  selectedTradeId,
  setSearch,
  setSelectedTradeId,
  tradeFilter,
  totalTrades,
}: {
  cycleTradeFilter: () => void;
  exportTradesCsv: () => void;
  filteredTrades: Trade[];
  search: string;
  selectedTradeId: number;
  setSearch: (value: string) => void;
  setSelectedTradeId: (id: number) => void;
  tradeFilter: TradeFilter;
  totalTrades: number;
}) {
  return (
    <section className="trades-panel">
      <div className="panel-header">
        <h2>Trades ({totalTrades})</h2>
        <div className="table-tools">
          <label className="search-box">
            <SearchIcon />
            <input placeholder="Search trades..." value={search} onChange={(event) => setSearch(event.target.value)} />
          </label>
          <button type="button" onClick={cycleTradeFilter}>
            <FilterIcon />
            {tradeFilter === 'all' ? 'All trades' : tradeFilter === 'winners' ? 'Winners' : 'Losers'}
          </button>
          <button type="button" onClick={exportTradesCsv}>
            <DownloadIcon />
            Export CSV
          </button>
          <MenuIcon />
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Entry Time</th>
              <th>Exit Time</th>
              <th>Side</th>
              <th>Entry</th>
              <th>Exit</th>
              <th>Qty</th>
              <th>PnL (pts)</th>
              <th>PnL ($)</th>
              <th>R Multiple</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {filteredTrades.map((trade) => (
              <tr
                className={selectedTradeId === trade.id ? 'is-selected' : ''}
                key={trade.id}
                onClick={() => setSelectedTradeId(trade.id)}
              >
                <td>{trade.id}</td>
                <td>{trade.entryTime}</td>
                <td>{trade.exitTime}</td>
                <td className={`side-${trade.side.toLowerCase()}`}>{trade.side}</td>
                <td>{trade.entry.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                <td>{trade.exit.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                <td>{trade.quantity}</td>
                <td className={trade.pnlPoints >= 0 ? 'positive' : 'negative'}>{formatSigned(trade.pnlPoints)}</td>
                <td className={trade.pnlDollars >= 0 ? 'positive' : 'negative'}>{formatCurrency(trade.pnlDollars)}</td>
                <td className={trade.rMultiple >= 0 ? 'positive' : 'negative'}>{trade.rMultiple.toFixed(2)}</td>
                <td>
                  <span className={`result-chip ${trade.pnlDollars >= 0 ? 'is-win' : 'is-loss'}`}>{trade.reason}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <footer className="table-footer">
        <span>
          Showing {filteredTrades.length ? 1 : 0} to {filteredTrades.length} of {totalTrades} trades
        </span>
        <div className="pagination">
          <button type="button" aria-label="Previous page">
            <ChevronLeftIcon />
          </button>
          <button className="is-active" type="button">
            1
          </button>
          <button type="button">2</button>
          <button type="button">3</button>
          <span>...</span>
          <button type="button">8</button>
          <button type="button" aria-label="Next page">
            <ChevronRightIcon />
          </button>
          <select aria-label="Rows per page">
            <option>10 / page</option>
            <option>25 / page</option>
          </select>
        </div>
      </footer>
    </section>
  );
}

function StrategyPanel({
  completedAt,
  dataSource,
  duration,
  fees,
  formData,
  strategy,
}: {
  completedAt: string;
  dataSource: string;
  duration: string;
  fees: string;
  formData: BacktestForm;
  strategy: (typeof strategyOptions)[number];
}) {
  return (
    <aside className="insight-panel">
      <section className="insight-hero">
        <div className="panel-title">
          <LightbulbIcon />
          <h2>Strategy Insights</h2>
        </div>
        <div className="regime-card">
          <div className="regime-ring">
            <span>72%</span>
          </div>
          <div>
            <h3>Trend regime</h3>
            <p>{strategy.summary}</p>
          </div>
        </div>
      </section>

      <section className="definition-list" aria-label="Strategy details">
        <h3>Strategy details</h3>
        <div>
          <span>Timeframe</span>
          <strong>{formData.timeframe}</strong>
        </div>
        <div>
          <span>Markets</span>
          <strong>{formData.symbol}</strong>
        </div>
        <div>
          <span>Direction</span>
          <strong>Long & Short</strong>
        </div>
        <div>
          <span>Session</span>
          <strong>RTH 09:30-16:00 ET</strong>
        </div>
        <div>
          <span>Data range</span>
          <strong>
            {formData.from} to {formData.to}
          </strong>
        </div>
      </section>

      <section className="breakdown-section">
        <h3>Performance Breakdown</h3>
        <InsightBar label="Trending" value="72%" width="82%" />
        <InsightBar label="Ranging" value="18%" width="42%" tone="negative" />
        <InsightBar label="Volatile" value="10%" width="25%" tone="negative" />
      </section>

      <section>
        <h3>Risk Management</h3>
        <ul className="risk-list">
          {strategy.risk.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="completion-card">
        <div className="completion-icon">
          <CheckIcon />
        </div>
        <div>
          <h3>Backtest completed</h3>
          <p>{completedAt}</p>
          <p>Duration: {duration}</p>
          <p>Data: {dataSource}</p>
          <p>Fees: {fees}</p>
        </div>
      </section>
    </aside>
  );
}

function InsightBar({ label, tone = 'positive', value, width }: { label: string; tone?: 'positive' | 'negative'; value: string; width: string }) {
  return (
    <div className="insight-bar">
      <span>{label}</span>
      <div>
        <i className={`bar-${tone}`} style={{ width }} />
      </div>
      <strong>{value}</strong>
    </div>
  );
}

function normalizeApiResults(data: any): BacktestResults {
  const metrics = data.metrics ?? {};
  const trades = Array.isArray(data.trades)
    ? data.trades.map((trade: any, index: number) => ({
        id: index + 1,
        entryTime: String(trade.entry_time ?? ''),
        exitTime: String(trade.exit_time ?? ''),
        side: Number(trade.position) >= 0 ? 'Long' : 'Short',
        entry: Number(trade.entry_price ?? 0),
        exit: Number(trade.exit_price ?? 0),
        quantity: 1,
        pnlPoints: Number(trade.pnl ?? 0),
        pnlDollars: Number(trade.pnl ?? 0) * 50,
        rMultiple: Number(trade.return ?? 0),
        reason: 'Signal change',
    }))
    : sampleResults.trades;
  const equity = normalizeSeries(data.equity_curve, sampleResults.equity);
  const buyHold = normalizeSeries(data.buy_hold_curve, sampleResults.buyHold);
  const winningTrades = trades.filter((trade: Trade) => trade.pnlDollars > 0);
  const losingTrades = trades.filter((trade: Trade) => trade.pnlDollars < 0);
  const averageWin = average(winningTrades.map((trade: Trade) => trade.pnlDollars));
  const averageLoss = average(losingTrades.map((trade: Trade) => trade.pnlDollars));

  return {
    ...sampleResults,
    completedAt: new Date().toLocaleString(),
    dataSource: data.data_source ?? sampleResults.dataSource,
    equity,
    buyHold,
    metrics: [
      { label: 'Total Return', value: toPercent(metrics.total_return), detail: 'Strategy return', tone: numberTone(metrics.total_return) },
      { label: 'Sharpe Ratio', value: toFixed(metrics.sharpe_ratio), detail: 'Daily annualized', tone: 'neutral' },
      { label: 'Max Drawdown', value: toPercent(metrics.max_drawdown), detail: 'Largest equity decline', tone: 'negative' },
      { label: 'Win Rate', value: toPercent(metrics.win_rate), detail: `${trades.length} trades`, tone: numberTone(metrics.win_rate) },
      { label: 'Net Profit', value: formatCurrency(Number(metrics.net_profit ?? 0)), detail: '1 contract model', tone: numberTone(metrics.net_profit) },
      { label: 'Total Trades', value: String(metrics.total_trades ?? trades.length), detail: 'Signal exits', tone: 'neutral' },
      { label: 'Avg Win', value: formatCurrency(averageWin), detail: `${formatCurrency(averageLoss)} avg loss`, tone: 'positive' },
    ],
    trades,
  };
}

function normalizeSeries(points: unknown, fallback: number[]) {
  if (!Array.isArray(points)) return fallback;
  const values = points.map((point: any) => Number(point.equity) * 100000).filter((value: number) => Number.isFinite(value));
  return values.length > 1 ? values : fallback;
}

function buildLinePath(values: number[], width: number, height: number) {
  if (values.length < 2) return `M 0 ${height} L ${width} ${height}`;

  const min = Math.min(...values, 70000);
  const max = Math.max(...values, 130000);
  const range = max - min || 1;

  return values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(' ');
}

function sliceSeriesForRange(values: number[], range: string) {
  const sizeByRange: Record<string, number> = {
    '1M': 8,
    '3M': 14,
    '6M': 22,
    YTD: 28,
    '1Y': 34,
    All: values.length,
  };
  const size = sizeByRange[range] ?? values.length;
  return values.slice(Math.max(0, values.length - size));
}

function average(values: number[]) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function moduleTitle(activeNav: string) {
  const titles: Record<string, string> = {
    Strategies: 'Strategy registry from the backend',
    Results: 'Last completed run',
    Exports: 'Download research artifacts',
    Notebook: 'Research notebook is not persisted yet',
    Settings: 'Server and broker configuration',
  };
  return titles[activeNav] ?? 'Module status';
}

function moduleDescription(activeNav: string) {
  const descriptions: Record<string, string> = {
    Strategies: 'The frontend reads the backend strategy registry so the available modules are no longer just decorative labels.',
    Results: 'This view reflects the latest successful backtest response currently held in app state.',
    Exports: 'CSV export is wired to the visible trades after search and win/loss filtering.',
    Notebook: 'This still needs a persistence layer before notes can be saved across sessions.',
    Settings: 'Broker credentials stay in .env on the server; the browser can only see source availability.',
  };
  return descriptions[activeNav] ?? 'The backtest workspace is the primary wired module right now.';
}

function formatSigned(value: number) {
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}`;
}

function formatCurrency(value: number) {
  return `${value < 0 ? '-' : ''}$${Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function toFixed(value: unknown) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed.toFixed(2) : '0.00';
}

function toPercent(value: unknown) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return '0.00%';
  return `${parsed > 0 ? '+' : ''}${(parsed * 100).toFixed(2)}%`;
}

function numberTone(value: unknown): Metric['tone'] {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed === 0) return 'neutral';
  return parsed > 0 ? 'positive' : 'negative';
}

function IconSvg({ children, className = '', viewBox = '0 0 24 24' }: { children: React.ReactNode; className?: string; viewBox?: string }) {
  return (
    <svg aria-hidden="true" className={`icon ${className}`} fill="none" viewBox={viewBox}>
      {children}
    </svg>
  );
}

function TrendIcon() {
  return (
    <IconSvg>
      <path d="M4 17l5-5 4 3 7-8" />
      <path d="M15 7h5v5" />
    </IconSvg>
  );
}

function ForgeIcon() {
  return (
    <IconSvg className="brand-icon" viewBox="0 0 28 28">
      <path d="M14 2.6 25 8.8v12.4L14 27 3 21.2V8.8z" />
      <path d="M14 7v13" />
      <path d="M9.3 13.8 14 7l4.7 6.8" />
      <path d="M8.4 20h7.2a4 4 0 0 0 4-4" />
    </IconSvg>
  );
}

function GridIcon() {
  return (
    <IconSvg>
      <rect height="6" rx="1.5" width="6" x="4" y="4" />
      <rect height="6" rx="1.5" width="6" x="14" y="4" />
      <rect height="6" rx="1.5" width="6" x="4" y="14" />
      <rect height="6" rx="1.5" width="6" x="14" y="14" />
    </IconSvg>
  );
}

function ClockIcon() {
  return (
    <IconSvg>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 7v5l4 2" />
    </IconSvg>
  );
}

function DownloadIcon() {
  return (
    <IconSvg>
      <path d="M12 4v10" />
      <path d="M8 10l4 4 4-4" />
      <path d="M5 19h14" />
    </IconSvg>
  );
}

function DocumentIcon() {
  return (
    <IconSvg>
      <path d="M7 4h7l4 4v12H7z" />
      <path d="M14 4v5h4" />
      <path d="M10 13h5M10 16h5" />
    </IconSvg>
  );
}

function CogIcon() {
  return (
    <IconSvg>
      <circle cx="12" cy="12" r="3" />
      <path d="M19 12a7 7 0 0 0-.1-1.1l2-1.5-2-3.4-2.4 1a7.9 7.9 0 0 0-1.9-1.1L14.2 3h-4.4l-.4 2.9c-.7.3-1.3.6-1.9 1.1L5.1 6l-2 3.4 2 1.5A7 7 0 0 0 5 12c0 .4 0 .8.1 1.1l-2 1.5 2 3.4 2.4-1c.6.5 1.2.8 1.9 1.1l.4 2.9h4.4l.4-2.9c.7-.3 1.3-.6 1.9-1.1l2.4 1 2-3.4-2-1.5c.1-.3.1-.7.1-1.1z" />
    </IconSvg>
  );
}

function HelpIcon() {
  return (
    <IconSvg>
      <circle cx="12" cy="12" r="8" />
      <path d="M9.8 9a2.4 2.4 0 0 1 4.6.8c0 1.8-2.4 2-2.4 3.7" />
      <path d="M12 17h.01" />
    </IconSvg>
  );
}

function UserIcon() {
  return (
    <IconSvg>
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 20a7 7 0 0 1 14 0" />
    </IconSvg>
  );
}

function LightbulbIcon() {
  return (
    <IconSvg>
      <path d="M9 18h6" />
      <path d="M10 22h4" />
      <path d="M8.5 14.5A6 6 0 1 1 15.5 14c-.8.7-1.1 1.4-1.2 2H9.7c-.1-.7-.4-1.2-1.2-1.5z" />
    </IconSvg>
  );
}

function ChartIcon() {
  return (
    <IconSvg>
      <path d="M4 19V5" />
      <path d="M4 19h16" />
      <path d="M7 15l4-4 3 2 5-7" />
    </IconSvg>
  );
}

function SunIcon() {
  return (
    <IconSvg>
      <circle cx="12" cy="12" r="3.5" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1" />
    </IconSvg>
  );
}

function PlayIcon() {
  return (
    <IconSvg>
      <path d="M9 6l10 6-10 6z" />
    </IconSvg>
  );
}

function ResetIcon() {
  return (
    <IconSvg>
      <path d="M7 7a7 7 0 1 1-1.4 8" />
      <path d="M7 3v4h4" />
    </IconSvg>
  );
}

function ChevronUpIcon() {
  return (
    <IconSvg>
      <path d="M7 14l5-5 5 5" />
    </IconSvg>
  );
}

function InfoIcon() {
  return (
    <IconSvg className="info-icon">
      <circle cx="12" cy="12" r="8" />
      <path d="M12 10v6M12 7h.01" />
    </IconSvg>
  );
}

function ExpandIcon() {
  return (
    <IconSvg>
      <path d="M8 4H4v4M4 4l6 6M16 20h4v-4M20 20l-6-6" />
    </IconSvg>
  );
}

function MenuIcon() {
  return (
    <IconSvg>
      <path d="M12 5h.01M12 12h.01M12 19h.01" />
    </IconSvg>
  );
}

function SearchIcon() {
  return (
    <IconSvg>
      <circle cx="11" cy="11" r="6" />
      <path d="M16 16l4 4" />
    </IconSvg>
  );
}

function FilterIcon() {
  return (
    <IconSvg>
      <path d="M4 6h16l-6 7v5l-4 2v-7z" />
    </IconSvg>
  );
}

function ChevronLeftIcon() {
  return (
    <IconSvg>
      <path d="M15 18l-6-6 6-6" />
    </IconSvg>
  );
}

function ChevronRightIcon() {
  return (
    <IconSvg>
      <path d="M9 6l6 6-6 6" />
    </IconSvg>
  );
}

function CheckIcon() {
  return (
    <IconSvg>
      <path d="M5 12l4 4L19 6" />
    </IconSvg>
  );
}

export default App;
