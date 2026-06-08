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
  source: 'sample' | 'coinbase' | 'yahoo' | 'tradovate' | 'polygon' | 'cache';
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

type ProviderField = {
  key: string;
  label: string;
  secret: boolean;
  configured: boolean;
  value: string;
};

type ProviderSettings = {
  key: string;
  label: string;
  description: string;
  configured: boolean;
  fields: ProviderField[];
};

type LiveSnapshot = {
  id: number;
  captured_at: string;
  snapshot_type: string;
  symbol: string;
  request: Record<string, string>;
};

type QuoteSummary = {
  symbol: string;
  security_type: string;
  description: string;
  quote_status: string;
  datetime: string;
  last: number | null;
  bid: number | null;
  ask: number | null;
  change: number | null;
  change_percent: number | null;
  volume: number | null;
  previous_close: number | null;
  source_note: string;
};

type LiveQuoteResult = {
  symbols: string;
  detailFlag: string;
  summary?: QuoteSummary[];
  data: unknown;
};

type SourceDiagnostic = {
  key: string;
  label: string;
  configured: boolean;
  status: 'ok' | 'ready' | 'empty' | 'error' | 'needs_config';
  rows: number;
  detail: string;
  preview: Record<string, unknown>;
  next_steps?: string[];
};

type PaperStrategy = 'forward_long' | 'forward_short' | 'observe_only';

type PaperForm = {
  name: string;
  symbol: string;
  strategy: PaperStrategy;
  quantity: string;
  initial_cash: string;
  mark_price: string;
  detailFlag: string;
};

type PaperMark = {
  id: number;
  session_id: number;
  captured_at: string;
  symbol: string;
  price: number;
  quantity: number;
  position: number;
  cash: number;
  equity: number;
  pnl: number;
  signal: string;
  source_snapshot_id?: number | null;
  price_source?: string;
};

type PaperSession = {
  id: number;
  created_at: string;
  name: string;
  symbol: string;
  strategy: PaperStrategy;
  quantity: number;
  initial_cash: number;
  status: string;
  notes: string;
  latest_mark?: PaperMark | null;
};

type OptionsForm = {
  symbol: string;
  from: string;
  to: string;
  source: 'sample' | 'coinbase' | 'yahoo' | 'tradovate' | 'polygon' | 'cache';
  timeframe: string;
  strategy: 'long_call' | 'long_put' | 'bull_call_spread' | 'bear_put_spread' | 'long_straddle';
  option_type: 'CALL' | 'PUT';
  strike: string;
  premium: string;
  short_strike: string;
  short_premium: string;
  contracts: string;
  multiplier: string;
};

type OptionsResult = {
  metrics: Record<string, number>;
  trades: Array<Record<string, unknown>>;
  assumptions: string[];
  data_source: string;
};

type CongressTrade = {
  chamber: string;
  transaction_date: string;
  member: string;
  ticker: string;
  transaction_type: string;
  amount: string;
};

type CongressResult = {
  metrics: Record<string, number>;
  trade_details: Array<Record<string, unknown>>;
  holding_days: number;
  message: string;
};

type CongressIngestSummary = {
  status: string;
  year: number;
  limit: number;
  counts: {
    house: number;
    senate: number;
    total: number;
  };
  house: {
    status: string;
    reports_available: number;
    reports_downloaded: number;
    parsed: number;
    inserted: number;
    errors: Array<Record<string, unknown>>;
  };
  senate: {
    status: string;
    parsed: number;
    inserted: number;
    errors: string[];
  };
};

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
  { label: 'Live Data', icon: <ChartIcon /> },
  { label: 'Data Sources', icon: <DatabaseIcon /> },
  { label: 'Paper Trade', icon: <ClockIcon /> },
  { label: 'Options', icon: <GridIcon /> },
  { label: 'Congress', icon: <DocumentIcon /> },
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
  const [sourceDiagnostics, setSourceDiagnostics] = useState<SourceDiagnostic[]>([]);
  const [sourceProbeMessage, setSourceProbeMessage] = useState('Source diagnostics have not been probed yet.');
  const [providerSettings, setProviderSettings] = useState<ProviderSettings[]>([]);
  const [providerForms, setProviderForms] = useState<Record<string, Record<string, string>>>({});
  const [savingProvider, setSavingProvider] = useState<string | null>(null);
  const [liveSymbols, setLiveSymbols] = useState('AAPL,SPY');
  const [liveQuote, setLiveQuote] = useState<LiveQuoteResult | null>(null);
  const [liveSnapshots, setLiveSnapshots] = useState<LiveSnapshot[]>([]);
  const [paperForm, setPaperForm] = useState<PaperForm>({
    name: 'AAPL forward validation',
    symbol: 'AAPL',
    strategy: 'forward_long',
    quantity: '1',
    initial_cash: '100000',
    mark_price: '',
    detailFlag: 'ALL',
  });
  const [paperSessions, setPaperSessions] = useState<PaperSession[]>([]);
  const [paperMarks, setPaperMarks] = useState<PaperMark[]>([]);
  const [selectedPaperSessionId, setSelectedPaperSessionId] = useState<number | null>(null);
  const [paperMessage, setPaperMessage] = useState('Create a paper session, then mark it from live quotes or a manual price.');
  const [oauthVerifier, setOauthVerifier] = useState('');
  const [oauthMessage, setOauthMessage] = useState('Start OAuth after saving your E*TRADE consumer key and secret.');
  const [oauthAuthorizeUrl, setOauthAuthorizeUrl] = useState('');
  const [optionForm, setOptionForm] = useState<OptionsForm>({
    symbol: 'ES',
    from: '2025-01-02',
    to: '2025-01-02',
    source: 'sample',
    timeframe: '1min',
    strategy: 'long_call',
    option_type: 'CALL',
    strike: '5300',
    premium: '12.50',
    short_strike: '5350',
    short_premium: '4.00',
    contracts: '1',
    multiplier: '100',
  });
  const [optionResults, setOptionResults] = useState<OptionsResult | null>(null);
  const [congressHoldingDays, setCongressHoldingDays] = useState('5');
  const [congressTrades, setCongressTrades] = useState<CongressTrade[]>([]);
  const [congressResult, setCongressResult] = useState<CongressResult | null>(null);
  const [congressIngestResult, setCongressIngestResult] = useState<CongressIngestSummary | null>(null);
  const [congressSyncing, setCongressSyncing] = useState(false);
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
        loadSourceDiagnostics(false),
        loadProviderSettings(),
        loadLiveSnapshots(),
        loadPaperSessions(),
        loadCongressTrades(),
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
      const source = value as BacktestForm['source'];
      if (source === 'coinbase') {
        setFormData((previous) => ({
          ...previous,
          source,
          symbol: 'BTC-USD',
          timeframe: '1d',
          from: '2025-01-02',
          to: '2025-01-31',
          strategy: 'ma_crossover',
          params: defaultParams.ma_crossover,
        }));
        return;
      }
      if (source === 'yahoo') {
        setFormData((previous) => ({
          ...previous,
          source,
          symbol: 'AAPL',
          timeframe: '1d',
          from: '2025-01-02',
          to: '2025-01-31',
          strategy: 'ma_crossover',
          params: defaultParams.ma_crossover,
        }));
        return;
      }
      setFormData((previous) => ({
        ...previous,
        source,
        symbol: source === 'polygon' ? 'AAPL' : source === 'sample' ? 'ES' : previous.symbol,
        timeframe: source === 'polygon' ? '1d' : previous.timeframe,
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

  const collectBacktestCandles = async () => {
    if (formData.source === 'cache') {
      setLastAction('Choose sample, Tradovate, or Polygon before collecting candles');
      return;
    }
    const data = await callApi<{ saved: { rows: number; inserted_or_updated: number }; rows: number; source: string }>(
      '/api/v1/market/candles/collect',
      {
        method: 'POST',
        body: JSON.stringify({
          source: formData.source,
          symbol: formData.symbol,
          timeframe: formData.timeframe,
          from: formData.from,
          to: formData.to,
        }),
      },
    );
    if (data?.saved) {
      setLastAction(`Cached ${data.saved.inserted_or_updated} ${data.source} candles`);
      loadSourceDiagnostics(false);
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

  const loadSourceDiagnostics = async (probe = false) => {
    setSourceProbeMessage(probe ? 'Probing configured sources...' : 'Loaded source configuration status.');
    const params = new URLSearchParams({ probe: String(probe) });
    const data = await callApi<{ sources: SourceDiagnostic[] }>(`/api/v1/data/sources?${params.toString()}`);
    if (data?.sources) {
      setSourceDiagnostics(data.sources);
      const errors = data.sources.filter((source) => source.status === 'error');
      const empty = data.sources.filter((source) => source.status === 'empty');
      const needsConfig = data.sources.filter((source) => source.status === 'needs_config');
      setSourceProbeMessage(
        probe
          ? `Probe complete: ${data.sources.filter((source) => source.status === 'ok').length} ok, ${needsConfig.length} need config, ${errors.length} error, ${empty.length} empty.`
          : 'Ready to probe configured data sources.',
      );
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

  const loadProviderSettings = async () => {
    const data = await callApi<{ providers: ProviderSettings[] }>('/api/v1/settings/providers');
    if (data?.providers) setProviderSettings(data.providers);
    return data;
  };

  const updateProviderField = (providerKey: string, fieldKey: string, value: string) => {
    setProviderForms((previous) => ({
      ...previous,
      [providerKey]: {
        ...(previous[providerKey] ?? {}),
        [fieldKey]: value,
      },
    }));
  };

  const saveProviderSettings = async (providerKey: string) => {
    setSavingProvider(providerKey);
    const data = await callApi<{ providers: ProviderSettings[] }>(`/api/v1/settings/providers/${providerKey}`, {
      method: 'POST',
      body: JSON.stringify({ values: providerForms[providerKey] ?? {} }),
    });
    if (data?.providers) {
      setProviderSettings(data.providers);
      setProviderForms((previous) => ({ ...previous, [providerKey]: {} }));
      const savedProvider = data.providers.find((provider) => provider.key === providerKey);
      setLastAction(`${savedProvider?.label ?? providerKey} settings saved`);
      const health = await callApi<ApiHealth>('/api/v1/health');
      if (health) setApiHealth(health);
    }
    setSavingProvider(null);
  };

  const clearProviderField = async (providerKey: string, fieldKey: string) => {
    setSavingProvider(providerKey);
    const data = await callApi<{ providers: ProviderSettings[] }>(`/api/v1/settings/providers/${providerKey}/clear`, {
      method: 'POST',
      body: JSON.stringify({ keys: [fieldKey] }),
    });
    if (data?.providers) {
      setProviderSettings(data.providers);
      setProviderForms((previous) => ({ ...previous, [providerKey]: { ...(previous[providerKey] ?? {}), [fieldKey]: '' } }));
      setLastAction(`${fieldKey} cleared`);
      const health = await callApi<ApiHealth>('/api/v1/health');
      if (health) setApiHealth(health);
      await loadSourceDiagnostics(false);
    }
    setSavingProvider(null);
  };

  const startEtradeOAuth = async () => {
    const data = await callApi<{ authorize_url: string; message: string }>('/api/v1/etrade/oauth/start', {
      method: 'POST',
    });
    if (data?.authorize_url) {
      setOauthMessage(data.message);
      setOauthAuthorizeUrl(data.authorize_url);
      window.open(data.authorize_url, '_blank', 'noopener,noreferrer');
    }
  };

  const completeEtradeOAuth = async () => {
    const data = await callApi<{ providers: ProviderSettings[]; message: string }>('/api/v1/etrade/oauth/complete', {
      method: 'POST',
      body: JSON.stringify({ verifier: oauthVerifier.trim() }),
    });
    if (data?.providers) {
      setProviderSettings(data.providers);
      setOauthVerifier('');
      setOauthMessage(data.message);
      setOauthAuthorizeUrl('');
      const health = await callApi<ApiHealth>('/api/v1/health');
      if (health) setApiHealth(health);
    }
  };

  const renewEtradeToken = async () => {
    const data = await callApi<{ message: string }>('/api/v1/etrade/oauth/renew', { method: 'POST' });
    if (data?.message) setOauthMessage(data.message);
  };

  const fetchLiveQuote = async () => {
    const params = new URLSearchParams({ symbols: liveSymbols, detailFlag: 'ALL' });
    const data = await callApi<LiveQuoteResult>(`/api/v1/etrade/live/quote?${params.toString()}`);
    if (data) {
      setLiveQuote(data);
      setLastAction(`Loaded live E*TRADE quote for ${data.symbols}`);
    }
  };

  const collectLiveQuote = async () => {
    const data = await callApi<{ data: unknown; summary?: QuoteSummary[]; snapshots: LiveSnapshot[] }>('/api/v1/etrade/live/collect', {
      method: 'POST',
      body: JSON.stringify({ symbols: liveSymbols, detailFlag: 'ALL' }),
    });
    if (data) {
      setLiveQuote({ symbols: liveSymbols, detailFlag: 'ALL', summary: data.summary, data: data.data });
      setLiveSnapshots(data.snapshots ?? []);
      setLastAction(`Collected E*TRADE quote snapshot for ${liveSymbols}`);
    }
  };

  const loadLiveSnapshots = async () => {
    const data = await callApi<{ snapshots: LiveSnapshot[] }>('/api/v1/etrade/live/snapshots');
    if (data?.snapshots) setLiveSnapshots(data.snapshots);
    return data;
  };

  const updatePaperField = (field: keyof PaperForm, value: string) => {
    if (field === 'strategy') {
      setPaperForm((previous) => ({
        ...previous,
        strategy: value as PaperStrategy,
      }));
      return;
    }
    setPaperForm((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const loadPaperSessions = async () => {
    const data = await callApi<{ sessions: PaperSession[] }>('/api/v1/paper/sessions');
    if (data?.sessions) {
      setPaperSessions(data.sessions);
      const selectedStillExists = data.sessions.some((session) => session.id === selectedPaperSessionId);
      const nextSelectedId = selectedStillExists ? selectedPaperSessionId : data.sessions[0]?.id ?? null;
      setSelectedPaperSessionId(nextSelectedId);
      if (nextSelectedId) await loadPaperMarks(nextSelectedId);
    }
    return data;
  };

  const loadPaperMarks = async (sessionId: number) => {
    const data = await callApi<{ marks: PaperMark[] }>(`/api/v1/paper/sessions/${sessionId}/marks`);
    if (data?.marks) setPaperMarks(data.marks);
    return data;
  };

  const createPaperSession = async () => {
    const payload = {
      name: paperForm.name,
      symbol: paperForm.symbol,
      strategy: paperForm.strategy,
      quantity: Number(paperForm.quantity),
      initial_cash: Number(paperForm.initial_cash),
    };
    const data = await callApi<{ session: PaperSession; sessions: PaperSession[] }>('/api/v1/paper/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (data?.session) {
      setPaperSessions(data.sessions ?? [data.session]);
      setSelectedPaperSessionId(data.session.id);
      setPaperMessage(`Created ${data.session.name}. Add a live or manual mark to start the forward trail.`);
      await loadPaperMarks(data.session.id);
      setLastAction(`Paper session created for ${data.session.symbol}`);
    }
  };

  const selectPaperSession = async (sessionId: number) => {
    setSelectedPaperSessionId(sessionId);
    await loadPaperMarks(sessionId);
  };

  const markPaperSession = async (mode: 'live' | 'manual') => {
    const sessionId = selectedPaperSessionId ?? paperSessions[0]?.id;
    if (!sessionId) {
      setPaperMessage('Create a paper session before marking price.');
      return;
    }

    const payload: { session_id: number; price?: number; detailFlag: string } = {
      session_id: sessionId,
      detailFlag: paperForm.detailFlag,
    };
    if (mode === 'manual') {
      payload.price = Number(paperForm.mark_price);
    }

    const data = await callApi<{ mark: PaperMark; marks: PaperMark[]; sessions: PaperSession[] }>('/api/v1/paper/mark', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (data?.mark) {
      setPaperSessions(data.sessions ?? paperSessions);
      setPaperMarks(data.marks ?? [data.mark, ...paperMarks]);
      setPaperMessage(
        `${data.mark.signal.replace(/_/g, ' ')} at ${formatCurrency(data.mark.price)}. Equity ${formatCurrency(data.mark.equity)}.`,
      );
      setLastAction(`Paper ${mode} mark saved for ${data.mark.symbol}`);
    }
  };

  const updateOptionField = (field: keyof OptionsForm, value: string) => {
    setOptionForm((previous) => {
      const next = { ...previous, [field]: value };
      if (field === 'strategy') {
        next.option_type = value.includes('put') ? 'PUT' : 'CALL';
      }
      if (field === 'source' && value === 'polygon') {
        next.symbol = 'AAPL';
        next.timeframe = '1d';
      }
      if (field === 'source' && value === 'coinbase') {
        next.symbol = 'BTC-USD';
        next.timeframe = '1d';
        next.from = '2025-01-02';
        next.to = '2025-01-10';
        next.strike = '95000';
        next.premium = '2500';
        next.short_strike = '100000';
        next.short_premium = '1000';
        next.multiplier = '1';
      }
      if (field === 'source' && value === 'yahoo') {
        next.symbol = 'AAPL';
        next.timeframe = '1d';
        next.from = '2025-01-02';
        next.to = '2025-01-31';
        next.strike = '240';
        next.premium = '12.50';
        next.short_strike = '260';
        next.short_premium = '4.00';
        next.multiplier = '100';
      }
      if (field === 'source' && value === 'sample') {
        next.symbol = 'ES';
      }
      return next;
    });
  };

  const runOptionsBacktest = async () => {
    const data = await callApi<OptionsResult>('/api/v1/options/backtest', {
      method: 'POST',
      body: JSON.stringify(optionForm),
    });
    if (data?.metrics) {
      setOptionResults(data);
      setLastAction(`Options ${optionForm.strategy.replace(/_/g, ' ')} replay complete`);
    }
  };

  const loadCongressTrades = async () => {
    const data = await callApi<{ trades: CongressTrade[] }>('/api/v1/congress/trades?limit=25');
    if (data?.trades) setCongressTrades(data.trades);
    return data;
  };

  const runCongressBacktest = async () => {
    const data = await callApi<CongressResult>('/api/v1/congress/backtest', {
      method: 'POST',
      body: JSON.stringify({ holding_days: Number(congressHoldingDays) }),
    });
    if (data?.metrics) {
      setCongressResult(data);
      setLastAction(`Congressional disclosure replay checked ${data.metrics.total_trades ?? 0} trades`);
    }
  };

  const syncCongressTrades = async () => {
    setCongressSyncing(true);
    const year = new Date().getFullYear();
    try {
      const data = await callApi<{ summary: CongressIngestSummary; trades: { trades: CongressTrade[] }; message: string }>(
        '/api/v1/congress/ingest',
        {
          method: 'POST',
          body: JSON.stringify({ year, limit: 25, include_senate: true }),
        },
      );
      if (data?.summary) {
        setCongressIngestResult(data.summary);
        setCongressTrades(data.trades?.trades ?? congressTrades);
        loadSourceDiagnostics(false);
        setLastAction(`Synced ${data.summary.counts.total} congressional disclosure rows`);
      }
    } finally {
      setCongressSyncing(false);
    }
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
            collectLiveQuote={collectLiveQuote}
            completeEtradeOAuth={completeEtradeOAuth}
            congressHoldingDays={congressHoldingDays}
            congressIngestResult={congressIngestResult}
            congressResult={congressResult}
            congressSyncing={congressSyncing}
            congressTrades={congressTrades}
            exportTradesCsv={exportTradesCsv}
            fetchLiveQuote={fetchLiveQuote}
            liveQuote={liveQuote}
            liveSnapshots={liveSnapshots}
            liveSymbols={liveSymbols}
            oauthMessage={oauthMessage}
            oauthAuthorizeUrl={oauthAuthorizeUrl}
            oauthVerifier={oauthVerifier}
            paperForm={paperForm}
            paperMarks={paperMarks}
            paperMessage={paperMessage}
            paperSessions={paperSessions}
            createPaperSession={createPaperSession}
            markPaperSession={markPaperSession}
            optionForm={optionForm}
            optionResults={optionResults}
            providerForms={providerForms}
            providerSettings={providerSettings}
            renewEtradeToken={renewEtradeToken}
            results={results}
            runCongressBacktest={runCongressBacktest}
            syncCongressTrades={syncCongressTrades}
            runOptionsBacktest={runOptionsBacktest}
            clearProviderField={clearProviderField}
            saveProviderSettings={saveProviderSettings}
            savingProvider={savingProvider}
            setCongressHoldingDays={setCongressHoldingDays}
            setLiveSymbols={setLiveSymbols}
            setOauthVerifier={setOauthVerifier}
            selectedPaperSessionId={selectedPaperSessionId}
            selectPaperSession={selectPaperSession}
            sourceDiagnostics={sourceDiagnostics}
            sourceProbeMessage={sourceProbeMessage}
            startEtradeOAuth={startEtradeOAuth}
            updateOptionField={updateOptionField}
            updatePaperField={updatePaperField}
            updateProviderField={updateProviderField}
            loadSourceDiagnostics={loadSourceDiagnostics}
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
                <option value="BTC-USD">BTC-USD - Bitcoin</option>
                <option value="ETH-USD">ETH-USD - Ethereum</option>
                <option value="AAPL">AAPL - Apple</option>
                <option value="SPY">SPY - S&P 500 ETF</option>
                <option value="QQQ">QQQ - Nasdaq 100 ETF</option>
                <option value="NVDA">NVDA - Nvidia</option>
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
                <option value="coinbase">Coinbase crypto</option>
                <option value="yahoo">Yahoo Finance</option>
                <option value="tradovate">Tradovate</option>
                <option value="polygon">Polygon</option>
                <option value="cache">Cached candles</option>
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
              <button className="reset-button" type="button" onClick={collectBacktestCandles} disabled={formData.source === 'cache'}>
                <DatabaseIcon />
                Collect candles
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

function QuoteSummaryList({ summaries }: { summaries: QuoteSummary[] }) {
  return (
    <div className="quote-summary-grid">
      {summaries.map((quote) => (
        <article className="quote-summary-card" key={`${quote.symbol}-${quote.datetime}`}>
          <div>
            <span>{quote.symbol || 'Unknown'}</span>
            <strong>{quote.description || quote.security_type || 'Quote'}</strong>
          </div>
          <ul>
            <li><span>Last</span><strong>{quote.last ? formatCurrency(quote.last) : 'n/a'}</strong></li>
            <li><span>Bid / ask</span><strong>{formatOptionalPrice(quote.bid)} / {formatOptionalPrice(quote.ask)}</strong></li>
            <li><span>Volume</span><strong>{quote.volume ? quote.volume.toLocaleString() : 'n/a'}</strong></li>
            <li><span>Status</span><strong>{quote.quote_status || 'n/a'}</strong></li>
          </ul>
          <p>{quote.datetime || quote.source_note}</p>
        </article>
      ))}
    </div>
  );
}

function ModulePanel({
  activeNav,
  apiHealth,
  backendStrategies,
  collectLiveQuote,
  completeEtradeOAuth,
  congressHoldingDays,
  congressIngestResult,
  congressResult,
  congressSyncing,
  congressTrades,
  exportTradesCsv,
  fetchLiveQuote,
  liveQuote,
  liveSnapshots,
  liveSymbols,
  oauthMessage,
  oauthAuthorizeUrl,
  oauthVerifier,
  paperForm,
  paperMarks,
  paperMessage,
  paperSessions,
  createPaperSession,
  markPaperSession,
  optionForm,
  optionResults,
  providerForms,
  providerSettings,
  renewEtradeToken,
  results,
  runCongressBacktest,
  syncCongressTrades,
  runOptionsBacktest,
  clearProviderField,
  saveProviderSettings,
  savingProvider,
  setCongressHoldingDays,
  setLiveSymbols,
  setOauthVerifier,
  selectedPaperSessionId,
  selectPaperSession,
  sourceDiagnostics,
  sourceProbeMessage,
  startEtradeOAuth,
  updateOptionField,
  updatePaperField,
  updateProviderField,
  loadSourceDiagnostics,
}: {
  activeNav: string;
  apiHealth: ApiHealth | null;
  backendStrategies: Array<{ key: string; label: string }>;
  collectLiveQuote: () => void;
  completeEtradeOAuth: () => void;
  createPaperSession: () => void;
  congressHoldingDays: string;
  congressIngestResult: CongressIngestSummary | null;
  congressResult: CongressResult | null;
  congressSyncing: boolean;
  congressTrades: CongressTrade[];
  exportTradesCsv: () => void;
  fetchLiveQuote: () => void;
  liveQuote: LiveQuoteResult | null;
  liveSnapshots: LiveSnapshot[];
  liveSymbols: string;
  markPaperSession: (mode: 'live' | 'manual') => void;
  oauthMessage: string;
  oauthAuthorizeUrl: string;
  oauthVerifier: string;
  paperForm: PaperForm;
  paperMarks: PaperMark[];
  paperMessage: string;
  paperSessions: PaperSession[];
  optionForm: OptionsForm;
  optionResults: OptionsResult | null;
  providerForms: Record<string, Record<string, string>>;
  providerSettings: ProviderSettings[];
  renewEtradeToken: () => void;
  results: BacktestResults;
  runCongressBacktest: () => void;
  syncCongressTrades: () => void;
  runOptionsBacktest: () => void;
  clearProviderField: (providerKey: string, fieldKey: string) => void;
  saveProviderSettings: (providerKey: string) => void;
  savingProvider: string | null;
  setCongressHoldingDays: (value: string) => void;
  setLiveSymbols: (value: string) => void;
  setOauthVerifier: (value: string) => void;
  selectedPaperSessionId: number | null;
  selectPaperSession: (sessionId: number) => void;
  sourceDiagnostics: SourceDiagnostic[];
  sourceProbeMessage: string;
  startEtradeOAuth: () => void;
  updateOptionField: (field: keyof OptionsForm, value: string) => void;
  updatePaperField: (field: keyof PaperForm, value: string) => void;
  updateProviderField: (providerKey: string, fieldKey: string, value: string) => void;
  loadSourceDiagnostics: (probe?: boolean) => void;
}) {
  const routeEntries = apiHealth ? Object.entries(apiHealth.routes) : [];
  const selectedPaperSession = paperSessions.find((session) => session.id === selectedPaperSessionId) ?? paperSessions[0] ?? null;

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
        {activeNav === 'Live Data' && (
          <>
            <article className="module-card is-wide">
              <div className="provider-card-header">
                <div>
                  <h3>E*TRADE OAuth connect</h3>
                  <p>{oauthMessage}</p>
                </div>
                <strong className={apiHealth?.sources?.etrade_market_data ? 'module-status-ok' : 'module-status-warn'}>
                  {apiHealth?.sources?.etrade_market_data ? 'Token ready' : 'Needs token'}
                </strong>
              </div>
              <div className="module-form-grid">
                <label className="provider-field">
                  <span>Verifier code</span>
                  <input
                    placeholder="Paste verifier after approving E*TRADE"
                    value={oauthVerifier}
                    onChange={(event) => setOauthVerifier(event.target.value)}
                  />
                </label>
              </div>
              {oauthAuthorizeUrl ? (
                <a className="oauth-link" href={oauthAuthorizeUrl} rel="noreferrer" target="_blank">
                  Open E*TRADE authorization
                </a>
              ) : null}
              <div className="action-row">
                <button className="run-button" type="button" onClick={startEtradeOAuth}>
                  <PlayIcon />
                  Connect E*TRADE
                </button>
                <button className="reset-button" type="button" onClick={completeEtradeOAuth}>
                  <CheckIcon />
                  Save token
                </button>
                <button className="reset-button" type="button" onClick={renewEtradeToken}>
                  <ResetIcon />
                  Renew
                </button>
              </div>
            </article>

            <article className="module-card">
              <h3>Live quote</h3>
              <label className="provider-field">
                <span>Symbols</span>
                <input value={liveSymbols} onChange={(event) => setLiveSymbols(event.target.value)} />
              </label>
              <div className="action-row">
                <button className="run-button" type="button" onClick={fetchLiveQuote}>
                  <ChartIcon />
                  Fetch quote
                </button>
                <button className="reset-button" type="button" onClick={collectLiveQuote}>
                  <DownloadIcon />
                  Collect
                </button>
              </div>
              {liveQuote?.summary?.length ? <QuoteSummaryList summaries={liveQuote.summary} /> : null}
              <pre className="live-json">{liveQuote ? summarizePayload(liveQuote.data) : 'No live quote loaded yet.'}</pre>
            </article>

            <article className="module-card">
              <h3>Saved snapshots</h3>
              <ul>
                {liveSnapshots.length ? (
                  liveSnapshots.map((snapshot) => (
                    <li key={snapshot.id}>
                      <span>{snapshot.symbol}</span>
                      <strong>{snapshot.snapshot_type} at {snapshot.captured_at}</strong>
                    </li>
                  ))
                ) : (
                  <li>
                    <span>No snapshots</span>
                    <strong>Collect a quote to start the database</strong>
                  </li>
                )}
              </ul>
            </article>
          </>
        )}

        {activeNav === 'Data Sources' && (
          <>
            <article className="module-card is-wide">
              <div className="provider-card-header">
                <div>
                  <h3>Source diagnostics</h3>
                  <p>{sourceProbeMessage}</p>
                </div>
                <strong className="module-status-ok">{sourceDiagnostics.length} sources</strong>
              </div>
              <div className="action-row">
                <button className="run-button" type="button" onClick={() => loadSourceDiagnostics(true)}>
                  <ChartIcon />
                  Probe sources
                </button>
                <button className="reset-button" type="button" onClick={() => loadSourceDiagnostics(false)}>
                  <ResetIcon />
                  Refresh status
                </button>
              </div>
            </article>

            {sourceDiagnostics.map((source) => (
              <article className="module-card" key={source.key}>
                <div className="provider-card-header">
                  <div>
                    <h3>{source.label}</h3>
                    <p>{source.detail}</p>
                  </div>
                  <strong className={source.status === 'ok' || source.status === 'ready' ? 'module-status-ok' : 'module-status-warn'}>
                    {source.status.replace(/_/g, ' ')}
                  </strong>
                </div>
                <ul>
                  <li><span>Configured</span><strong>{source.configured ? 'yes' : 'no'}</strong></li>
                  <li><span>Rows / records</span><strong>{source.rows.toLocaleString()}</strong></li>
                  <li><span>Source key</span><strong>{source.key}</strong></li>
                </ul>
                {source.next_steps?.length ? (
                  <div className="next-steps">
                    <span>Next steps</span>
                    <ol>
                      {source.next_steps.map((step) => (
                        <li key={step}>{step}</li>
                      ))}
                    </ol>
                  </div>
                ) : null}
                <pre className="live-json">{summarizePayload(source.preview)}</pre>
              </article>
            ))}
          </>
        )}

        {activeNav === 'Paper Trade' && (
          <>
            <article className="module-card is-wide">
              <div className="provider-card-header">
                <div>
                  <h3>Forward paper session</h3>
                  <p>{paperMessage}</p>
                </div>
                <strong className="module-status-ok">Paper only</strong>
              </div>
              <div className="module-form-grid">
                <label className="provider-field">
                  <span>Name</span>
                  <input value={paperForm.name} onChange={(event) => updatePaperField('name', event.target.value)} />
                </label>
                <label className="provider-field">
                  <span>Symbol</span>
                  <input value={paperForm.symbol} onChange={(event) => updatePaperField('symbol', event.target.value)} />
                </label>
                <label className="provider-field">
                  <span>Forward model</span>
                  <select value={paperForm.strategy} onChange={(event) => updatePaperField('strategy', event.target.value)}>
                    <option value="forward_long">Forward long</option>
                    <option value="forward_short">Forward short</option>
                    <option value="observe_only">Observe only</option>
                  </select>
                </label>
                <label className="provider-field">
                  <span>Quantity</span>
                  <input type="number" min="0.0001" step="0.0001" value={paperForm.quantity} onChange={(event) => updatePaperField('quantity', event.target.value)} />
                </label>
                <label className="provider-field">
                  <span>Initial cash</span>
                  <input type="number" min="1" value={paperForm.initial_cash} onChange={(event) => updatePaperField('initial_cash', event.target.value)} />
                </label>
                <label className="provider-field">
                  <span>Manual mark price</span>
                  <input type="number" min="0.0001" step="0.0001" placeholder="Optional test price" value={paperForm.mark_price} onChange={(event) => updatePaperField('mark_price', event.target.value)} />
                </label>
              </div>
              <div className="action-row">
                <button className="run-button" type="button" onClick={createPaperSession}>
                  <CheckIcon />
                  Create session
                </button>
                <button className="reset-button" type="button" onClick={() => markPaperSession('live')} disabled={!selectedPaperSession}>
                  <ChartIcon />
                  Mark live quote
                </button>
                <button className="reset-button" type="button" onClick={() => markPaperSession('manual')} disabled={!selectedPaperSession}>
                  <ClockIcon />
                  Mark manual
                </button>
              </div>
            </article>

            <article className="module-card">
              <h3>Paper sessions</h3>
              <ul className="paper-session-list">
                {paperSessions.length ? (
                  paperSessions.map((session) => (
                    <li key={session.id}>
                      <button
                        className={`paper-session-button ${selectedPaperSession?.id === session.id ? 'is-active' : ''}`}
                        onClick={() => selectPaperSession(session.id)}
                        type="button"
                      >
                        <span>{session.name}</span>
                        <strong>
                          {session.symbol} · {formatPaperStrategy(session.strategy)}
                        </strong>
                        <em>{session.latest_mark ? `${formatCurrency(session.latest_mark.equity)} equity` : 'No marks yet'}</em>
                      </button>
                    </li>
                  ))
                ) : (
                  <li>
                    <span>No paper sessions</span>
                    <strong>Create one to start forward validation</strong>
                  </li>
                )}
              </ul>
            </article>

            <article className="module-card">
              <h3>Equity marks</h3>
              <ul>
                {paperMarks.length ? (
                  paperMarks.slice(0, 8).map((mark) => (
                    <li key={mark.id}>
                      <span>{mark.captured_at} · {mark.signal.replace(/_/g, ' ')}</span>
                      <strong>
                        {formatCurrency(mark.equity)} · {formatCurrency(mark.pnl)}
                      </strong>
                    </li>
                  ))
                ) : (
                  <li>
                    <span>No marks saved</span>
                    <strong>Use live or manual mark</strong>
                  </li>
                )}
              </ul>
            </article>

            <article className="module-card">
              <h3>Validation role</h3>
              <p>
                Use this to collect a future equity trail from real quote marks after a backtest. It validates direction and mark-to-market behavior,
                but full candle-based signal replay still needs scheduled bar aggregation.
              </p>
            </article>
          </>
        )}

        {activeNav === 'Options' && (
          <>
            <article className="module-card is-wide">
              <h3>Options strategy replay</h3>
              <div className="module-form-grid">
                <label className="provider-field">
                  <span>Symbol</span>
                  <input value={optionForm.symbol} onChange={(event) => updateOptionField('symbol', event.target.value)} />
                </label>
                <label className="provider-field">
                  <span>Strategy</span>
                  <select value={optionForm.strategy} onChange={(event) => updateOptionField('strategy', event.target.value)}>
                    <option value="long_call">Long call</option>
                    <option value="long_put">Long put</option>
                    <option value="bull_call_spread">Bull call spread</option>
                    <option value="bear_put_spread">Bear put spread</option>
                    <option value="long_straddle">Long straddle</option>
                  </select>
                </label>
                <label className="provider-field">
                  <span>From</span>
                  <input type="date" value={optionForm.from} onChange={(event) => updateOptionField('from', event.target.value)} />
                </label>
                <label className="provider-field">
                  <span>To</span>
                  <input type="date" value={optionForm.to} onChange={(event) => updateOptionField('to', event.target.value)} />
                </label>
                <label className="provider-field">
                  <span>Data source</span>
                  <select value={optionForm.source} onChange={(event) => updateOptionField('source', event.target.value)}>
                    <option value="sample">Sample CSV</option>
                    <option value="coinbase">Coinbase crypto</option>
                    <option value="yahoo">Yahoo Finance</option>
                    <option value="tradovate">Tradovate</option>
                    <option value="polygon">Polygon</option>
                    <option value="cache">Cached candles</option>
                  </select>
                </label>
                <label className="provider-field">
                  <span>Strike</span>
                  <input value={optionForm.strike} onChange={(event) => updateOptionField('strike', event.target.value)} />
                </label>
                <label className="provider-field">
                  <span>Premium / debit</span>
                  <input value={optionForm.premium} onChange={(event) => updateOptionField('premium', event.target.value)} />
                </label>
                <label className="provider-field">
                  <span>Short strike</span>
                  <input value={optionForm.short_strike} onChange={(event) => updateOptionField('short_strike', event.target.value)} />
                </label>
                <label className="provider-field">
                  <span>Short premium</span>
                  <input value={optionForm.short_premium} onChange={(event) => updateOptionField('short_premium', event.target.value)} />
                </label>
                <label className="provider-field">
                  <span>Contracts</span>
                  <input value={optionForm.contracts} onChange={(event) => updateOptionField('contracts', event.target.value)} />
                </label>
              </div>
              <button className="run-button" type="button" onClick={runOptionsBacktest}>
                <PlayIcon />
                Run options replay
              </button>
            </article>

            <article className="module-card">
              <h3>Options result</h3>
              {optionResults ? (
                <ul>
                  <li><span>Total return</span><strong>{toPercent(optionResults.metrics.total_return)}</strong></li>
                  <li><span>Net profit</span><strong>{formatCurrency(optionResults.metrics.net_profit ?? 0)}</strong></li>
                  <li><span>Win rate</span><strong>{toPercent(optionResults.metrics.win_rate)}</strong></li>
                  <li><span>Entry cost</span><strong>{formatCurrency(optionResults.metrics.entry_cost ?? 0)}</strong></li>
                </ul>
              ) : (
                <p>Run a strategy replay to see the payoff proxy and assumptions.</p>
              )}
            </article>

            <article className="module-card">
              <h3>Model assumptions</h3>
              <ul>
                {(optionResults?.assumptions ?? [
                  'Uses underlying OHLCV close values.',
                  'No historical option bid/ask, IV, theta decay, assignment, liquidity, or slippage.',
                  'Still simulation-only; no orders are placed.',
                ]).map((assumption) => (
                  <li key={assumption}>
                    <span>{assumption}</span>
                    <strong>simulation</strong>
                  </li>
                ))}
              </ul>
            </article>
          </>
        )}

        {activeNav === 'Congress' && (
          <>
            <article className="module-card">
              <h3>Congressional disclosure replay</h3>
              <button className="reset-button" type="button" onClick={syncCongressTrades} disabled={congressSyncing}>
                <DownloadIcon />
                {congressSyncing ? 'Syncing' : 'Sync disclosures'}
              </button>
              <label className="provider-field">
                <span>Holding days</span>
                <input value={congressHoldingDays} onChange={(event) => setCongressHoldingDays(event.target.value)} />
              </label>
              <button className="run-button" type="button" onClick={runCongressBacktest}>
                <PlayIcon />
                Run congress replay
              </button>
              <p>{congressResult?.message ?? 'Uses House/Senate disclosures from the local SQLite database.'}</p>
            </article>

            <article className="module-card">
              <h3>Congress metrics</h3>
              {congressResult ? (
                <ul>
                  <li><span>Total trades</span><strong>{String(congressResult.metrics.total_trades ?? 0)}</strong></li>
                  <li><span>Total return</span><strong>{toPercent(congressResult.metrics.total_return)}</strong></li>
                  <li><span>Average return</span><strong>{toPercent(congressResult.metrics.average_return)}</strong></li>
                  <li><span>Win rate</span><strong>{toPercent(congressResult.metrics.win_rate)}</strong></li>
                </ul>
              ) : (
                <p>No congressional replay has been run in this session yet.</p>
              )}
            </article>

            <article className="module-card">
              <h3>Disclosure sync</h3>
              {congressIngestResult ? (
                <ul>
                  <li><span>Total rows</span><strong>{congressIngestResult.counts.total.toLocaleString()}</strong></li>
                  <li><span>House parsed</span><strong>{congressIngestResult.house.parsed.toLocaleString()}</strong></li>
                  <li><span>House inserted</span><strong>{congressIngestResult.house.inserted.toLocaleString()}</strong></li>
                  <li><span>Senate status</span><strong>{congressIngestResult.senate.status.replace(/_/g, ' ')}</strong></li>
                </ul>
              ) : (
                <p>Sync recent House PTR PDFs and Senate eFD-derived summaries before replaying disclosures.</p>
              )}
            </article>

            <article className="module-card is-wide">
              <h3>Stored disclosures</h3>
              <ul>
                {congressTrades.length ? (
                  congressTrades.slice(0, 10).map((trade) => (
                    <li key={`${trade.chamber}-${trade.member}-${trade.ticker}-${trade.transaction_date}`}>
                      <span>{trade.transaction_date} · {trade.member} · {trade.ticker}</span>
                      <strong>{trade.chamber} {trade.transaction_type} {trade.amount}</strong>
                    </li>
                  ))
                ) : (
                  <li>
                    <span>No stored disclosures</span>
                    <strong>Run scrapers before backtesting</strong>
                  </li>
                )}
              </ul>
            </article>
          </>
        )}

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

        {activeNav === 'Settings' &&
          providerSettings.map((provider) => (
            <article className="module-card provider-card" key={provider.key}>
              <div className="provider-card-header">
                <div>
                  <h3>{provider.label}</h3>
                  <p>{provider.description}</p>
                </div>
                <strong className={provider.configured ? 'module-status-ok' : 'module-status-warn'}>
                  {provider.configured ? 'Configured' : 'Missing keys'}
                </strong>
              </div>

              <div className="provider-fields">
                {provider.fields.map((field) => (
                  <label className="provider-field" key={field.key}>
                    <span>
                      {field.label}
                      {field.configured && field.secret ? <small> saved as {field.value}</small> : null}
                    </span>
                    {field.key === 'ETRADE_ENV' ? (
                      <select
                        value={providerForms[provider.key]?.[field.key] ?? field.value ?? 'sandbox'}
                        onChange={(event) => updateProviderField(provider.key, field.key, event.target.value)}
                      >
                        <option value="sandbox">sandbox</option>
                        <option value="live">live</option>
                      </select>
                    ) : (
                      <div className="provider-input-row">
                        <input
                          autoComplete="off"
                          placeholder={field.secret ? (field.configured ? 'Leave blank to keep saved value' : 'Paste key or secret') : field.value}
                          type={field.secret ? 'password' : 'text'}
                          value={providerForms[provider.key]?.[field.key] ?? (field.secret ? '' : field.value ?? '')}
                          onChange={(event) => updateProviderField(provider.key, field.key, event.target.value)}
                        />
                        {field.secret && field.configured ? (
                          <button
                            aria-label={`Clear ${field.label}`}
                            className="field-clear-button"
                            disabled={savingProvider === provider.key}
                            onClick={() => clearProviderField(provider.key, field.key)}
                            type="button"
                          >
                            Clear
                          </button>
                        ) : null}
                      </div>
                    )}
                  </label>
                ))}
              </div>

              <button className="run-button" type="button" onClick={() => saveProviderSettings(provider.key)} disabled={savingProvider === provider.key}>
                <CheckIcon />
                {savingProvider === provider.key ? 'Saving...' : `Save ${provider.label}`}
              </button>
            </article>
          ))}

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

function summarizePayload(payload: unknown) {
  const text = JSON.stringify(payload, null, 2);
  if (!text) return 'No payload.';
  return text.length > 1400 ? `${text.slice(0, 1400)}\n...` : text;
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
    'Live Data': 'E*TRADE live market data collection',
    'Data Sources': 'Market data source diagnostics',
    'Paper Trade': 'Forward paper validation',
    Options: 'Options strategy replay',
    Congress: 'Congressional disclosure backtesting',
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
    'Live Data': 'Connect E*TRADE through OAuth, fetch quote snapshots, and save them into the local market-data collection store.',
    'Data Sources': 'Probe every configured source, inspect row counts, and see source-specific errors before trusting a backtest.',
    'Paper Trade': 'Create paper-only sessions, mark them with live E*TRADE quotes or manual prices, and compare the future equity trail against your backtest thesis.',
    Options: 'Replay option payoff strategies against the same underlying candle sources used by the backtest engine.',
    Congress: 'Review locally stored congressional disclosures and replay them against deterministic futures proxies.',
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

function formatPaperStrategy(strategy: PaperStrategy) {
  return strategy.replace(/_/g, ' ');
}

function formatCurrency(value: number) {
  return `${value < 0 ? '-' : ''}$${Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatOptionalPrice(value: number | null) {
  return typeof value === 'number' && Number.isFinite(value) ? formatCurrency(value) : 'n/a';
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

function DatabaseIcon() {
  return (
    <IconSvg>
      <ellipse cx="12" cy="5" rx="7" ry="3" />
      <path d="M5 5v6c0 1.7 3.1 3 7 3s7-1.3 7-3V5" />
      <path d="M5 11v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" />
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
