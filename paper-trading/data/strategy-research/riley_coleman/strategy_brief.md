# Transcript-Derived Strategy Brief

This is a research artifact for private backtesting. It is not trading advice, a performance claim, or a transcript republication.

Generated at: `2026-06-17T12:40:41.649279+00:00`
Videos with usable transcript segments: `80`

## Candidate Rules

### fixed_risk_reward_management

- Type: `risk`
- Confidence: `0.982`
- Evidence count: `3704` across `78` videos
- Rule: Define stop, target, and risk/reward before entry.
- Mechanical translation: Attach bracket orders with ATR/structure stop, fixed R multiple target, max hold bars, and no-entry if reward is too small.

### session_timing_filter

- Type: `filter`
- Confidence: `0.974`
- Evidence count: `4070` across `77` videos
- Rule: Prefer specific futures/scalping windows instead of trading every minute of the session.
- Mechanical translation: Restrict entries to configured session windows and reject low-liquidity chop periods.

### use_market_structure_bias

- Type: `filter`
- Confidence: `0.965`
- Evidence count: `6478` across `76` videos
- Rule: Use market structure, trend, channel, or directional bias to avoid fighting the dominant move.
- Mechanical translation: Add a trend filter based on swing structure, EMA slope, higher highs/lows, or channel direction.

### trade_from_key_zones

- Type: `context`
- Confidence: `0.965`
- Evidence count: `6308` across `76` videos
- Rule: Only look for trades at pre-identified support, resistance, structure, liquidity, or supply/demand zones.
- Mechanical translation: Build rolling support/resistance zones from prior swing highs/lows; ignore signals that occur away from those zones.

### avoid_bad_context

- Type: `risk`
- Confidence: `0.956`
- Evidence count: `2305` across `75` videos
- Rule: Avoid trades during unclear, choppy, or news-driven conditions.
- Mechanical translation: Add no-trade filters for low range/volume chop, major scheduled events, and setups without clean invalidation.

### wait_for_rejection_confirmation

- Type: `entry`
- Confidence: `0.851`
- Evidence count: `1683` across `63` videos
- Rule: Wait for price rejection or confirmation before entering instead of buying/selling the first touch.
- Mechanical translation: Require a rejection candle, wick rejection, engulfing candle, close back through the level, or volume confirmation after a zone test.

### break_and_retest

- Type: `entry`
- Confidence: `0.843`
- Evidence count: `986` across `62` videos
- Rule: Treat break-and-retest behavior as a separate setup from pure reversal entries.
- Mechanical translation: After a level breaks with momentum, mark it as pending and enter only if price retests that level within a fixed bar window.

## Highest-Signal Evidence Pointers

### fixed_risk_reward_management
- `00:14:10` [How To Trade Futures For Beginners (Full Guide)](https://www.youtube.com/watch?v=-Iw-nCNAlTg) - keywords: stop
- `00:07:16` [LIVE TRADING FUTURES Losing $805 (This Was Rough...)](https://www.youtube.com/watch?v=-edI0gXN918) - keywords: target
- `00:01:12` [The Strategy I'd Use To Flip $4 Into $100,000](https://www.youtube.com/watch?v=-xuQXmQWMCk) - keywords: stop
- `00:00:37` [I Tried Making $33,000 in 33 Days Trading Futures](https://www.youtube.com/watch?v=0XoYhKlBEVs) - keywords: target
- `00:09:53` [Complete Futures Trading Strategy For Beginners](https://www.youtube.com/watch?v=2LnFWQ10-0E) - keywords: stop

### session_timing_filter
- `00:00:02` [How To Trade Futures For Beginners (Full Guide)](https://www.youtube.com/watch?v=-Iw-nCNAlTg) - keywords: morning
- `00:00:03` [LIVE TRADING FUTURES Losing $805 (This Was Rough...)](https://www.youtube.com/watch?v=-edI0gXN918) - keywords: morning
- `00:02:27` [The Strategy I'd Use To Flip $4 Into $100,000](https://www.youtube.com/watch?v=-xuQXmQWMCk) - keywords: open, morning
- `00:00:21` [I Tried Making $33,000 in 33 Days Trading Futures](https://www.youtube.com/watch?v=0XoYhKlBEVs) - keywords: open
- `00:00:07` [Complete Futures Trading Strategy For Beginners](https://www.youtube.com/watch?v=2LnFWQ10-0E) - keywords: morning

### use_market_structure_bias
- `00:24:39` [How To Trade Futures For Beginners (Full Guide)](https://www.youtube.com/watch?v=-Iw-nCNAlTg) - keywords: trend
- `00:00:46` [LIVE TRADING FUTURES Losing $805 (This Was Rough...)](https://www.youtube.com/watch?v=-edI0gXN918) - keywords: trend
- `00:02:54` [The Strategy I'd Use To Flip $4 Into $100,000](https://www.youtube.com/watch?v=-xuQXmQWMCk) - keywords: bias
- `00:01:27` [I Tried Making $33,000 in 33 Days Trading Futures](https://www.youtube.com/watch?v=0XoYhKlBEVs) - keywords: trend
- `00:02:03` [Complete Futures Trading Strategy For Beginners](https://www.youtube.com/watch?v=2LnFWQ10-0E) - keywords: trend

### trade_from_key_zones
- `00:23:14` [How To Trade Futures For Beginners (Full Guide)](https://www.youtube.com/watch?v=-Iw-nCNAlTg) - keywords: key area
- `00:00:18` [LIVE TRADING FUTURES Losing $805 (This Was Rough...)](https://www.youtube.com/watch?v=-edI0gXN918) - keywords: level
- `00:00:41` [The Strategy I'd Use To Flip $4 Into $100,000](https://www.youtube.com/watch?v=-xuQXmQWMCk) - keywords: level
- `00:03:36` [I Tried Making $33,000 in 33 Days Trading Futures](https://www.youtube.com/watch?v=0XoYhKlBEVs) - keywords: zone
- `00:03:25` [Complete Futures Trading Strategy For Beginners](https://www.youtube.com/watch?v=2LnFWQ10-0E) - keywords: level

### avoid_bad_context
- `00:15:57` [How To Trade Futures For Beginners (Full Guide)](https://www.youtube.com/watch?v=-Iw-nCNAlTg) - keywords: news
- `00:02:54` [LIVE TRADING FUTURES Losing $805 (This Was Rough...)](https://www.youtube.com/watch?v=-edI0gXN918) - keywords: news
- `00:03:28` [The Strategy I'd Use To Flip $4 Into $100,000](https://www.youtube.com/watch?v=-xuQXmQWMCk) - keywords: don't trade
- `00:00:55` [I Tried Making $33,000 in 33 Days Trading Futures](https://www.youtube.com/watch?v=0XoYhKlBEVs) - keywords: chop, choppy
- `00:01:15` [Complete Futures Trading Strategy For Beginners](https://www.youtube.com/watch?v=2LnFWQ10-0E) - keywords: news

### wait_for_rejection_confirmation
- `00:24:49` [How To Trade Futures For Beginners (Full Guide)](https://www.youtube.com/watch?v=-Iw-nCNAlTg) - keywords: confirm
- `00:01:57` [LIVE TRADING FUTURES Losing $805 (This Was Rough...)](https://www.youtube.com/watch?v=-edI0gXN918) - keywords: failed
- `00:15:12` [The Strategy I'd Use To Flip $4 Into $100,000](https://www.youtube.com/watch?v=-xuQXmQWMCk) - keywords: confirmation, confirm
- `00:02:09` [I Tried Making $33,000 in 33 Days Trading Futures](https://www.youtube.com/watch?v=0XoYhKlBEVs) - keywords: confirm
- `00:08:37` [Complete Futures Trading Strategy For Beginners](https://www.youtube.com/watch?v=2LnFWQ10-0E) - keywords: confirmation, confirm

### break_and_retest
- `00:20:20` [How To Trade Futures For Beginners (Full Guide)](https://www.youtube.com/watch?v=-Iw-nCNAlTg) - keywords: flip
- `00:03:09` [The Strategy I'd Use To Flip $4 Into $100,000](https://www.youtube.com/watch?v=-xuQXmQWMCk) - keywords: breakout
- `00:11:15` [I Tried Making $33,000 in 33 Days Trading Futures](https://www.youtube.com/watch?v=0XoYhKlBEVs) - keywords: retest
- `00:04:37` [Complete Futures Trading Strategy For Beginners](https://www.youtube.com/watch?v=2LnFWQ10-0E) - keywords: retest
- `00:00:47` [1 Minute Scalping Strategy (Only Takes 60 Minutes a Day)](https://www.youtube.com/watch?v=2Qz0hZfW6Ck) - keywords: breakout

## Ambiguities To Resolve Before Coding

- Discretionary chart drawing must be converted into fixed swing/zone definitions before backtesting.
- Any mention of profitability or win rate must be ignored unless reproduced after costs in our data.
- If transcripts emphasize order flow, Level 2/time-and-sales data is required; OHLCV proxies should be marked as lower confidence.
