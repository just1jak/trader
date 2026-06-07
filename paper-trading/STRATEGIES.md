# Trading Strategies for Backtesting

## 1. Moving Average Crossover (MA Cross)
- **Description**: Buy when short-term MA crosses above long-term MA; sell (or short) when it crosses below.
- **Parameters**: `fast` (short period), `slow` (long period)
- **Typical values**: fast=9, slow=21 (for intraday); fast=50, slow=200 (daily)
- **Implementation**: See `backend/api/strategies/ma_crossover.py`

## 2. Relative Strength Index (RSI)
- **Description**: Momentum oscillator measuring speed and change of price movements. RSI > 70 indicates overbought (sell signal); RSI < 30 indicates oversold (buy signal).
- **Parameters**: `period` (default 14), `overbought` (default 70), `oversold` (default 30)
- **Signal logic**: 
  - Buy when RSI crosses above `oversold` from below.
  - Sell/short when RSI crosses below `overbought` from above.
- **Implementation**: To be added.

## 3. Bollinger Bands
- **Description**: Volatility bands placed above and below a moving average. Price touching upper band may indicate overbought; lower band oversold.
- **Parameters**: `period` (default 20), `std_dev` (default 2)
- **Signal logic**:
  - Buy when price crosses below lower band and then closes back inside (mean reversion).
  - Sell when price crosses above upper band and then closes back inside.
- **Implementation**: To be added.

## 4. MACD (Moving Average Convergence Divergence)
- **Description**: Trend-following momentum indicator showing relationship between two EMAs.
- **Parameters**: `fast` (default 12), `slow` (default 26), `signal` (default 9)
- **Signal logic**:
  - Buy when MACD line crosses above signal line.
  - Sell when MACD line crosses below signal line.
- **Implementation**: To be added.

## 5. Breakout (Donchian Channel)
- **Description**: Buy when price breaks above the highest high of the last N periods; sell when breaks below lowest low.
- **Parameters**: `period` (default 20)
- **Signal logic**:
  - Buy when close > max(high, lookback=period)
  - Sell/short when close < min(low, lookback=period)
- **Implementation**: To be added.

## Scalping Strategies (short‑timeframe)

### 6. VWAP Mean‑Reversion
- **Description**: Trade price back to the volume‑weighted average price (VWAP) when it deviates beyond a set z‑score threshold.
- **Parameters**: `vwap_period` (rolling window for VWAP, default 20), `entry_z` (z‑score to enter, default 1.5), `exit_z` (z‑score to exit, default 0.5), `attenuate` (scale position as z‑score shrinks, default false).
- **Implementation**: See `backend/api/strategies/vwap_mr.py`

### 7. Opening Range Breakout (ORB)
- **Description**: Buy/sell when price breaks the high/low of the first N minutes after the session open, with an ATR‑based filter.
- **Parameters**: `orb_minutes` (length of opening range, default 30), `breakout_mult` (ATR multiplier for breakout filter, default 0.5).
- **Implementation**: See `backend/api/strategies/orb.py`

### 8. Order‑Flow Imbalance (Delta‑Scalp)
- **Description**: Go long when buying volume exceeds selling volume (positive delta) and short when selling dominates. Uses a smoothed delta‑volume ratio.
- **Parameters**: `delta_threshold` (threshold for normalized delta, default 0.5), `delta_ma_period` (smoothing period, default 10).
- **Note**: Requires a `delta` column (buy volume – sell volume). If missing, the strategy approximates delta as `(close‑open) * volume`.
- **Implementation**: See `backend/api/strategies/delta_scalp.py`

### 9. Micro‑Trend EMA Scalp
- **Description**: Very fast EMA crossover (e.g., 3‑ vs 8‑period) with a maximum hold‑time to force scalping‑style exits.
- **Parameters**: `fast` (fast EMA period, default 3), `slow` (slow EMA period, default 8), `max_hold_bars` (maximum bars to stay in a position, default 5).
- **Implementation**: See `backend/api/strategies/ema_scalp.py`

### 10. Support/Resistance Flip
- **Description**: Detect swing highs/lows, wait for a breakout, then enter on a retest of the broken level (now acting as support or resistance).
- **Parameters**: `lookback` (period to detect swing high/low, default 20), `retest_tolerance` (price tolerance for retest, default 0.5 price units).
- **Implementation**: See `backend/api/strategies/support_resistance_flip.py`

## 11. Volume Profile and Order Flow
- **Description**: Combines volume profile analysis (identifying high/low volume nodes, POC, value area) with order flow metrics (delta, cumulative delta, absorption) to identify high-probability breakout and reversal zones based on where actual trading activity occurs.
- **Parameters**: 
  - `lookback_period` (number of bars for volume profile calculation, default 20)
  - `price_bin_size` (tick size for volume binning, default 0.25 for ES)
  - `volume_threshold` (minimum volume for significant node, default 2.0 x average bin volume)
  - `delta_threshold` (threshold for normalized delta signal, default 0.5)
  - `delta_ma_period` (smoothing period for delta, default 10)
  - `lv_breakout_volume_mult` (volume confirmation multiplier for LVN breaks, default 1.5)
- **Signal Logic**:
  - Long: Price breaks above LVN with volume > (average volume * lv_breakout_volume_mult) AND positive delta absorption
  - Short: Price breaks below LVN with volume > (average volume * lv_breakout_volume_mult) AND negative delta absorption
  - Long: Price tests POC from below with buying absorption (delta > 0 on retest)
  - Short: Price tests POC from above with selling absorption (delta < 0 on retest)
  - Exit: Target next HVN or opposite VA boundary; stop loss just inside broken LVN or beyond absorption level
- **Note**: Requires time/sales data for accurate delta calculation. Approximates delta as (close-open)*volume when direct data unavailable.
- **Implementation**: See `backend/api/strategies/volume_profile_orderflow.py`

## How to Add a New Strategy
1. Create a Python file under `backend/api/strategies/` (e.g., `rsi.py`).
2. Implement a function `generate_signals(data: pd.DataFrame, params: dict) -> pd.Series` that returns a Series with same index as `data` and values: 1 (long), -1 (short), 0 (flat).
3. Ensure the strategy name matches the filename (without `.py`).
4. Restart the backend (or reload if using development mode).
5. Use the strategy name in the UI or API call.