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

## 12. Riley Coleman-Inspired Reversal Scalp
- **Description**: Mechanical futures scalping model based on recurring Riley Coleman public-video themes: support/resistance zones, reversal timing windows, rejection candles, break-and-retest entries, and fixed risk/reward trade management.
- **Parameters**:
  - `zone_lookback` (bars used to identify prior support/resistance, default 50)
  - `atr_period` (ATR period for dynamic tolerance/stops, default 14)
  - `atr_tolerance_mult` (zone tolerance as ATR multiple when `retest_tolerance` is 0, default 0.35)
  - `retest_tolerance` (fixed price-unit tolerance; 0 uses ATR tolerance, default 0)
  - `volume_mult` (minimum volume multiple versus recent average, default 1.05)
  - `wick_ratio` (minimum rejection wick relative to body, default 1.2)
  - `risk_reward` (target multiple of initial risk, default 1.75)
  - `stop_atr_mult` (stop distance as ATR multiple, default 1.0)
  - `max_hold_bars` (maximum bars in a scalp, default 20)
  - `use_time_filter` (restrict entries to reversal windows, default true)
  - `reversal_windows` (comma-separated intraday windows, default `09:35-11:00,13:30-15:45`)
  - `enable_break_retest` (allow breakout then retest entries, default true)
  - `trend_filter` and `trend_ema` (optional trend-bias filter)
- **Signal Logic**:
  - Long: price tests prior demand/support, closes back above the zone, prints a bullish rejection candle, and volume confirms.
  - Short: price tests prior supply/resistance, closes back below the zone, prints a bearish rejection candle, and volume confirms.
  - Optional: after a breakout, wait for a retest of the broken level before entering in the breakout direction.
  - Exit: ATR stop, risk/reward target, opposite setup, or max-hold timeout.
- **Source Note**: See `riley-coleman-reversal-scalp.md`
- **Implementation**: See `backend/api/strategies/riley_coleman_reversal.py`

## 13. Riley Coleman Transcript-Strict Morning Scalp
- **Description**: Strict mechanical futures scalp distilled from 80 Riley Coleman public-video transcripts. Requires morning/session timing, trend/structure bias, prior key level, breakout/retest or failed-break confirmation, chop avoidance, and fixed risk/reward management.
- **Parameters**:
  - `session_windows` (entry windows, default `09:35-11:15`)
  - `zone_lookback` (bars used to identify prior support/resistance, default 45)
  - `atr_period` (ATR period for buffers, tolerance, and stops, default 14)
  - `volume_mult` and `confirmation_volume_mult` (breakout/retest volume gates)
  - `ema_fast`, `ema_slow`, and `min_trend_atr_mult` (trend/structure bias gates)
  - `chop_range_atr_mult` (minimum prior range versus ATR to avoid chop)
  - `breakout_atr_mult`, `retest_atr_mult`, and `min_body_atr_mult` (breakout/retest strictness)
  - `retest_expiry_bars` (bars allowed between breakout and retest, default 8)
  - `risk_reward`, `stop_atr_mult`, and `max_hold_bars` (trade management)
  - `allow_failed_breakout` (allow failed breakout/trap entries, default true)
  - `require_intraday_time` (disable entries without intraday timestamps, default true)
- **Signal Logic**:
  - Long: during the morning window, fast EMA/structure bias is bullish, recent range is not chop, price breaks above prior resistance on volume, then retests the broken level and prints bullish confirmation.
  - Short: mirror the long logic below prior support with bearish bias and bearish confirmation.
  - Optional failed-break entries: price breaks a key level, fails back through it, and confirms in the opposite direction with aligned bias.
  - Exit: fixed initial risk, `risk_reward` target, trend-bias loss, or max-hold timeout.
- **Source Note**: See `riley-coleman-transcript-strict.md` and `data/strategy-research/riley_coleman/strategy_brief.md`
- **Implementation**: See `backend/api/strategies/riley_coleman_transcript_strict.py`

## 14. Futures Analytica-Inspired Order Flow Spread
- **Description**: Mechanical Level 2 / footprint strategy inspired by public Futures Analytica material around L2Azimuth, DEX Array, Trespass, Polarity ATI, and order-flow imbalance trading.
- **Parameters**:
  - `depth_levels` (number of bid/ask depth levels to aggregate, default 5)
  - `imbalance_threshold` (normalized bid/ask imbalance needed for pressure, default 0.5)
  - `microprob_threshold` (optional directional forecast gate, default 0.8)
  - `spoofing_max` (optional maximum spoofing score, default 0.4)
  - `spread_max_ticks` and `tick_size` (spread-quality gate)
  - `large_order_mult` (large in-spread order threshold versus rolling average, default 2.0)
  - `saturation_z` (unusual volume/order-flow saturation threshold, default 1.2)
  - `delta_threshold` (normalized delta pressure threshold, default 0.35)
  - `risk_reward`, `stop_atr_mult`, and `max_hold_bars` (short-hold execution management)
  - `require_in_spread_order` (only enter on real in-spread order columns when true)
  - `allow_ohlcv_proxy` (fallback to candle/volume/delta proxies when L2 columns are missing)
- **Preferred Data Columns**:
  - `best_bid`, `best_ask`, `bid_size_1...N`, `ask_size_1...N` or `bid_depth`/`ask_depth`
  - `order_price`, `order_size`, `order_side`
  - `delta`
  - optional gates: `spoofing_score`, `microprobability`, `microprobability_direction`, `hf_omega`
- **Signal Logic**:
  - Long: bid-side depth/flow pressure or buy-side in-spread aggression, footprint confirmation, acceptable spread, low spoofing score, aligned microprobability/omega gate.
  - Short: ask-side pressure or sell-side in-spread aggression with the same confirmation/gating structure.
  - Exit: ATR stop, risk/reward target, opposite setup, book-pressure fade, or max-hold timeout.
- **Source Note**: See `futures-analytica-orderflow-spread.md`
- **Implementation**: See `backend/api/strategies/futures_analytica_orderflow_spread.py`

## How to Add a New Strategy
1. Create a Python file under `backend/api/strategies/` (e.g., `rsi.py`).
2. Implement a function `generate_signals(data: pd.DataFrame, params: dict) -> pd.Series` that returns a Series with same index as `data` and values: 1 (long), -1 (short), 0 (flat).
3. Ensure the strategy name matches the filename (without `.py`).
4. Restart the backend (or reload if using development mode).
5. Use the strategy name in the UI or API call.
