# Riley Coleman-Inspired Reversal Scalp

This is a mechanical backtest interpretation of recurring public Riley Coleman futures/scalping themes. It is not a transcript copy, trading advice, or an endorsement of the performance claims in the videos.

## Source Notes

I checked several Riley Coleman YouTube videos and attempted to retrieve captions from YouTube's advertised caption tracks. YouTube returned empty timed-text responses and `FAILED_PRECONDITION` from the transcript panel endpoint in this environment, so the implementation is based on available video metadata, descriptions, chapters, and common repeated themes rather than stored transcripts.

Primary sources reviewed:

- [Complete Futures Trading Strategy For Beginners](https://www.youtube.com/watch?v=2LnFWQ10-0E) - chapters emphasize reversal timings, profiting from those timings, a five-step entry process, and profit management.
- [The BEST 1 Minute Scalping Strategy EVER (Simple & Proven)](https://www.youtube.com/watch?v=NcWVdKkIMbM) - chapters emphasize profitable zones, an A+ checklist, and a timing trick.
- [Scalping Trading For Beginners (Full Course)](https://www.youtube.com/watch?v=KrM4CS4_ZtI) - chapters emphasize avoiding scalping mistakes, reading the market, directional signals, advanced patterns, and worked examples.
- [How To Read Futures Charts (With ZERO Experience)](https://www.youtube.com/watch?v=5Y7XCkXf7fk) - chapters emphasize market structure, trend lines/channels, support/resistance, key structures, and futures-market differences.

## Highlights Converted To Rules

- Trade only around actionable zones, not random candles.
- Build zones from prior support/resistance, then look for rejection or break-and-retest behavior.
- Prefer confirmation from candle rejection and above-average volume.
- Allow optional intraday timing windows for the reversal/timing idea.
- Keep trade management mechanical: ATR-based stop, risk/reward target, max hold, and exit on opposite setup.

## Backtest Implementation

Strategy file: `backend/api/strategies/riley_coleman_reversal.py`

Strategy name for API/UI: `riley_coleman_reversal`

Default behavior:

- Finds support/resistance from the prior `zone_lookback` bars.
- Enters long when price tests demand/support, prints a bullish rejection candle, and volume confirms.
- Enters short when price tests supply/resistance, prints a bearish rejection candle, and volume confirms.
- Optionally tracks breakouts and enters on retests of the broken level.
- Optionally filters entries to `reversal_windows`.
- Exits on ATR stop, risk/reward target, opposite setup, or `max_hold_bars`.

Important defaults:

- `zone_lookback`: `50`
- `atr_period`: `14`
- `atr_tolerance_mult`: `0.35`
- `volume_mult`: `1.05`
- `wick_ratio`: `1.2`
- `risk_reward`: `1.75`
- `stop_atr_mult`: `1.0`
- `max_hold_bars`: `20`
- `use_time_filter`: `true`
- `reversal_windows`: `09:35-11:00,13:30-15:45`
- `enable_break_retest`: `true`

## Notes

The strategy is intentionally conservative and testable. It does not attempt to reproduce discretionary chart drawing exactly, because backtests need fixed definitions. Use this as a research harness, then validate against real 1-minute futures data with fees, slippage, contract values, and session handling before paper trading.
