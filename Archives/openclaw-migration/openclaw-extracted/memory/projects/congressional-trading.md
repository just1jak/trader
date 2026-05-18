# Congressional Trading - Project Memory

## Status
Development phase. Scrapers, backtester, and Flask web app built. SQLite DB not yet initialized. Using placeholder data — real STOP Act endpoints not yet wired.

## Key Decisions
- 2026-04-26: Architecture set — scrape House/Senate disclosures, map tickers to futures proxies, backtest returns via Flask web app.

## Blockers
- SQLite database needs initialization (schema exists, DB does not)
- Scrapers using placeholder URLs, not real STOP Act endpoints
- Ticker-to-futures mapping needs expansion

## Research Findings
- House data source: house.gov/stock-watcher-data/xml/
- Senate data source: senate.gov/stockwatcher/
- Current trade data files: house_trades.json, senate_trades.json (as of 2026-04-26)

## Contacts & Leads
- None yet.

## Revenue Notes
- Potential alpha from front-running congressional disclosure lag
- Could feed signals into paper trading bot (futures channel)

## Conversation Log
- 2026-04-26: Initial project setup. No heartbeat messages sent yet.
