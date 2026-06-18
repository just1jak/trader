# Riley Coleman Transcript-Strict Morning Scalp

This strategy is a strict, mechanical backtest rule distilled from a larger
public Riley Coleman video transcript corpus. It is not trading advice, a
performance claim, or an endorsement of any video claims.

## Source Corpus

The transcript pipeline fetched and distilled `80` Riley Coleman channel videos.
The current generated artifacts are:

- `paper-trading/data/strategy-research/riley_coleman/strategy_spec.json`
- `paper-trading/data/strategy-research/riley_coleman/evidence.jsonl`
- `paper-trading/data/strategy-research/riley_coleman/strategy_brief.md`

Expanded evidence coverage from the generated spec:

- Fixed risk/reward management: `78` of `80` videos
- Morning/session timing: `77` of `80` videos
- Market structure or trend bias: `76` of `80` videos
- Key support/resistance or supply/demand zones: `76` of `80` videos
- Avoiding chop/news/bad context: `75` of `80` videos
- Rejection/confirmation: `63` of `80` videos
- Breakout, flip, or retest behavior: `62` of `80` videos

## Strict Backtest Rule

Strategy module:

```text
paper-trading/backend/api/strategies/riley_coleman_transcript_strict.py
```

Strategy name for API/UI:

```text
riley_coleman_transcript_strict
```

### Entry Gate

The strategy takes no trade unless all of these are true:

1. The timestamp is inside `session_windows`, default `09:35-11:15`.
2. Trend/structure bias agrees with the trade direction.
3. The market is not classified as chop by recent range versus ATR.
4. Price is interacting with a prior rolling support/resistance level.
5. The setup is either:
   - a breakout through the level followed by a retest and confirmation, or
   - a failed breakout/trap back through the level when enabled.
6. Volume confirms the breakout and retest conditions.

### Long Break/Retest

1. Prior resistance is the rolling high over `zone_lookback` bars, shifted so it
   cannot use the current bar.
2. Breakout bar closes above that resistance by `breakout_atr_mult * ATR`.
3. Fast EMA is above slow EMA, the fast EMA slope is positive, and EMA separation
   exceeds `min_trend_atr_mult * ATR`.
4. Volume is at least `volume_mult` times recent average volume.
5. Within `retest_expiry_bars`, price retests the broken level within
   `retest_atr_mult * ATR`.
6. Confirmation candle closes bullish and above its candle midpoint.

### Short Break/Retest

The short side mirrors the long side using prior support, bearish EMA bias,
downside breakout, retest from below, and bearish confirmation.

### Failed Breakouts

When `allow_failed_breakout` is true:

- Long: price breaks below support, then closes back above support with bullish
  confirmation and long bias.
- Short: price breaks above resistance, then closes back below resistance with
  bearish confirmation and short bias.

### Exits

On entry, the strategy sets a mechanical stop and target:

- Initial risk is the maximum of ATR stop distance, structure distance, and
  retest tolerance.
- Target is `risk_reward` times that initial risk.
- Exit when stop, target, trend-bias loss, or `max_hold_bars` triggers.

## Why This Is Separate From The Earlier Riley Strategy

`riley_coleman_reversal.py` is a broader exploratory harness for reversals and
break/retest ideas. This strict version intentionally requires more filters at
once so failed backtests are more informative. If it does not survive fees,
slippage, and out-of-sample testing, the rule should be rejected or revised from
evidence rather than loosened by hand.
