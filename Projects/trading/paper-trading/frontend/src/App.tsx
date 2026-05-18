import React, { useState } from 'react';
import { useApi } from './hooks/useApi';

function App() {
  const { callApi, loading, error } = useApi();
  const [formData, setFormData] = useState({
    symbol: 'ES',
    from: '2025-01-02',
    to: '2025-03-31',
    timeframe: '1min',
    strategy: 'ma_crossover',
    params: { fast: 9, slow: 21 }
  });
  const [results, setResults] = useState<any>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handleParamChange = (param: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      params: {
        ...prev.params,
        [param]: parseInt(value, 10) || 0
      }
    }));
  };

  const runBacktest = async () => {
    const data = await callApi('/backtest', {
      method: 'POST',
      body: JSON.stringify(formData)
    });
    if (data) {
      setResults(data);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Paper Trading Backtester</h1>
      <div>
        <h2>Configuration</h2>
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
          <div>
            <label>Symbol: </label>
            <input
              name="symbol"
              value={formData.symbol}
              onChange={handleChange}
              style={{ marginLeft: '8px' }}
            />
          </div>
          <div>
            <label>From: </label>
            <input
              type="date"
              name="from"
              value={formData.from}
              onChange={handleChange}
              style={{ marginLeft: '8px' }}
            />
          </div>
          <div>
            <label>To: </label>
            <input
              type="date"
              name="to"
              value={formData.to}
              onChange={handleChange}
              style={{ marginLeft: '8px' }}
            />
          </div>
          <div>
            <label>Timeframe: </label>
            <select
              name="timeframe"
              value={formData.timeframe}
              onChange={handleChange}
              style={{ marginLeft: '8px' }}
            >
              <option value="1min">1 min</option>
              <option value="5min">5 min</option>
              <option value="15min">15 min</option>
              <option value="1h">1 hour</option>
              <option value="1d">1 day</option>
            </select>
          </div>
          <div>
            <label>Strategy: </label>
            <select
              name="strategy"
              value={formData.strategy}
              onChange={handleChange}
              style={{ marginLeft: '8px' }}
            >
              <option value="ma_crossover">MA Crossover</option>
              <option value="vwap_mr">VWAP Mean‑Reversion</option>
              <option value="orb">Opening Range Breakout</option>
              <option value="delta_scalp">Order‑Flow Imbalance (Delta‑Scalp)</option>
              <option value="ema_scalp">Micro‑Trend EMA Scalp</option>
              <option value="support_resistance_flip">Support/Resistance Flip</option>
            </select>
          </div>
        </div>
        <div style={{ marginTop: '16px' }}>
          <h3>Strategy Parameters</h3>
          <div>
            <label>Fast MA: </label>
            <input
              type="number"
              value={formData.params.fast || ''}
              onChange={(e) => handleParamChange('fast', e.target.value)}
              style={{ marginLeft: '8px', width: '60px' }}
            />
          </div>
          <div>
            <label>Slow MA: </label>
            <input
              type="number"
              value={formData.params.slow || ''}
              onChange={(e) => handleParamChange('slow', e.target.value)}
              style={{ marginLeft: '8px', width: '60px' }}
            />
          </div>
        </div>
        <button onClick={runBacktest} disabled={loading} style={{ marginTop: '16px', padding: '8px 16px' }}>
          {loading ? 'Running...' : 'Run Backtest'}
        </button>
      </div>

      {error && <div style={{ color: 'red', marginTop: '16px' }}>Error: {error}</div>}

      {results && (
        <div style={{ marginTop: '32px' }}>
          <h2>Results</h2>
          <div>
            <h3>Metrics</h3>
            <ul>
              {Object.entries(results.metrics).map(([key, value]: [string, any]) => (
                <li key={key}>
                  {key}: {typeof value === 'number' ? value.toFixed(4) : value}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3>Equity Curve (first 10 points)</h3>
            <pre>{JSON.stringify(results.equity_curve.slice(0, 10), null, 2)}</pre>
          </div>
          <div>
            <h3>Trades</h3>
            {results.trades.length > 0 ? (
              <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                <thead>
                  <tr>
                    <th style={{ border: '1px solid #ccc', padding: '8px', textAlign: 'left' }}>Entry Time</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px', textAlign: 'left' }}>Exit Time</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px', textAlign: 'left' }}>Entry Price</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px', textAlign: 'left' }}>Exit Price</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px', textAlign: 'left' }}>Position</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px', textAlign: 'left' }}>PnL</th>
                  </tr>
                </thead>
                <tbody>
                  {results.trades.map((trade: any, idx: number) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ border: '1px solid #ccc', padding: '8px' }}>{trade.entry_time}</td>
                      <td style={{ border: '1px solid #ccc', padding: '8px' }}>{trade.exit_time}</td>
                      <td style={{ border: '1px solid #ccc', padding: '8px' }}>{trade.entry_price.toFixed(2)}</td>
                      <td style={{ border: '1px solid #ccc', padding: '8px' }}>{trade.exit_price.toFixed(2)}</td>
                      <td style={{ border: '1px solid #ccc', padding: '8px' }}>{trade.position}</td>
                      <td style={{ border: '1px solid #ccc', padding: '8px' }}>{trade.pnl.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>No trades executed.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;