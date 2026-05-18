# Trading: Congressional, Options, Crypto, Futures

Consolidated trading strategy + automation pipeline.

## Current Projects

- **congressional-trading** — house/senate trade tracking + backtesting
- **paper-trading** — pre-live simulation environment

## Roadmap

1. **Paper-trading validation** — confirm strategies in paper market (no real capital)
2. **LLM feedback loop** — train bot using market signals + news
3. **Options/crypto scalping** — add new instruments to strategy set
4. **Futures integration** — add leverage strategies
5. **Live bot deployment** — automated trading with proper risk controls

## Tech

- Python scrapers (congress_trades.db)
- Backtester (backtest.py)
- Paper trading backend + frontend
- Hermes automation for signal generation

## Key Files

- `congressional/congress_trades.db` — live house/senate trades
- `paper-trading/` — simulation backend + UI
