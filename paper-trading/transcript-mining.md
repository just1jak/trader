# Transcript Mining To Strategy Pipeline

This pipeline turns public YouTube captions into a traceable research artifact
before any rules are added to the backtester. The goal is to avoid guessing from
titles, thumbnails, or creator marketing language.

## What It Produces

`paper-trading/tools/transcript_strategy_miner.py` can produce:

- Raw caption files and metadata under `paper-trading/data/transcripts/...`
- `strategy_spec.json` with candidate rules, confidence, and source coverage
- `evidence.jsonl` with video/timestamp pointers for each extracted concept
- `strategy_brief.md` with a readable summary of the repeated rules

The generated brief is not a transcript republication and should not be treated
as trading advice or a performance claim. It is an evidence map for private
backtesting.

## Fetch Captions

Install `yt-dlp` if it is not already available:

```bash
python3 -m pip install yt-dlp
```

Fetch a channel or playlist:

```bash
python3 paper-trading/tools/transcript_strategy_miner.py all \
  --channel-url "https://www.youtube.com/@RileyColeman/videos" \
  --limit 20
```

Fetch a curated list of specific videos:

```bash
python3 paper-trading/tools/transcript_strategy_miner.py all \
  --urls-file paper-trading/data/transcripts/riley_video_urls.txt
```

The URL file should contain one video URL per line. Blank lines and lines
starting with `#` are ignored.

## Distill Existing Transcripts

If captions were downloaded elsewhere or copied in manually as `.vtt`, `.txt`,
or `.json`, run:

```bash
python3 paper-trading/tools/transcript_strategy_miner.py distill \
  --transcripts-dir paper-trading/data/transcripts/riley_coleman \
  --out-dir paper-trading/data/strategy-research/riley_coleman
```

## Backtest Handoff

Only promote a transcript-derived rule to code when it passes these checks:

1. It appears across multiple videos or receives very clear timestamped support.
2. It can be translated into a deterministic market-data condition.
3. It can be tested without lookahead bias.
4. It defines entry, invalidation, risk, and exit behavior.
5. It can survive futures costs: tick value, commissions, slippage, and realistic fills.

The expected implementation target is a strategy module under:

```text
paper-trading/backend/api/strategies/
```

The module should expose:

```python
def generate_signals(data: pd.DataFrame, params: dict) -> pd.Series:
    ...
```

Use `paper-trading/backend/api/strategies/riley_coleman_reversal.py` as the
current strategy harness, then update it only after the distilled evidence
supports a clearer rule.

## Failure Modes

- YouTube may advertise captions but return empty caption bodies from some
  hosts or environments.
- Auto-generated captions can mishear trading terms, so the output should be
  reviewed before coding.
- Discretionary ideas like "draw a good level" must become fixed swing/zone
  logic before a backtest can mean anything.
- If the creator relies on order flow, footprint, or Level 2 context, OHLCV-only
  rules are lower-confidence approximations.
