# Paper Trading Web App

A Flask + React application for backtesting and paper trading strategies across local samples, broker/provider data, and cached candle replays.

## Features
- Backtesting engine with pluggable strategies
- Historical data fetch from Coinbase crypto candles, Yahoo Finance stock candles, Tradovate, and Polygon
- Read-only E*TRADE quote and options-chain API layer
- Settings page for E*TRADE, Tradovate, and Polygon provider credentials
- Live Data page for E*TRADE OAuth connect, live quote fetch, and snapshot collection
- Data Sources page for readiness probes, row counts, previews, and provider errors
- Local OHLCV candle cache for collected provider bars
- Paper Trade page for forward paper validation with live quote marks or manual prices
- Options page for long call/put, spread, and straddle payoff simulations
- Congress page for House PTR sync, Senate eFD-derived sync, and local congressional disclosure replay
- React UI for configuring and visualizing backtests
- Dockerized for easy deployment

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Tradovate API credentials for futures candles, or Polygon API credentials for stock aggregate candles
- E*TRADE API credentials only if you want quote snapshots, options chains, or live quote marks
- No external credentials are needed for the local sample CSV source, Coinbase crypto candles, or Yahoo Finance stock/ETF candles

### Setup
1. Copy `.env.example` to `.env` and fill in your secrets.
2. Run `docker compose up --build`
3. Backend API available at `http://localhost:5000`
4. Frontend available at `http://localhost:5173`

If port `5000` is already taken, use an alternate backend port and point Vite at it:

```bash
cd backend
PORT=5001 python3 app.py

cd ../frontend
npm run dev
```

## Provider Settings

Use the frontend `Settings` page to enter provider details. The backend saves those values into `paper-trading/.env`; secret values are masked when returned to the browser, and blank saved secret inputs keep their existing value.
Saved secret fields can also be cleared explicitly from `Settings`, which is useful for removing expired E*TRADE access tokens before reconnecting OAuth.

Supported settings today:

- E*TRADE OAuth market-data credentials for quotes, expirations, and option chains.
- Tradovate credentials for historical futures candles: `TRADOVATE_USERNAME`, `TRADOVATE_PASSWORD`, `TRADOVATE_BASE_URL`, `TRADOVATE_APP_ID`, `TRADOVATE_APP_VERSION`, `TRADOVATE_DEVICE_ID`, plus optional `TRADOVATE_CID` and `TRADOVATE_SECRET` when your app registration provides API app credentials. Legacy `TRADOVATE_API_KEY` and `TRADOVATE_API_SECRET` are still accepted as username/password fallbacks, but the named username/password fields are preferred.
- Polygon API key and optional base URL for historical stock aggregate bars.

Docker compose mounts `.env` into the backend container so Settings changes persist across rebuilds.

## Live Data And Strategy Modules

- `Data Sources`: shows which sources are configured, whether probes succeed, how many local rows exist, the latest sample/error returned by each provider, and source-specific next steps.
- `Data Sources` also includes `Full check`, which calls `/api/v1/data/smoke-test` for a read-only source verification matrix. Passing sources are currently usable; blocked sources need credentials or a fresh provider authorization.
- `Data Sources` includes `Collect defaults`, which seeds safe local data: sample ES, Coinbase BTC-USD, Yahoo AAPL, and any configured Tradovate, Polygon, or E*TRADE source. It also shows cached datasets and a candle-row preview so you can confirm what was actually stored.
- `Data Sources` includes a source workbench for custom symbol/date requests. It can preview or collect OHLCV candles from sample, Coinbase, Yahoo Finance, Tradovate, Polygon, or cache, and it can fetch or collect E*TRADE quote snapshots.
- `Backtest`: choose a provider/date range and use `Collect candles` to store OHLCV bars locally. Coinbase crypto candles, Yahoo Finance stock candles, and the sample CSV work without API keys. Use `Cached candles` as the source to replay stored data without another provider call.
- `Live Data`: save E*TRADE consumer credentials in `Settings`, click `Connect E*TRADE`, paste the verifier code, then fetch or collect quote snapshots. Collected snapshots are stored in `data/market_data.sqlite`.
- `Paper Trade`: create a forward paper session, then mark it from an E*TRADE live quote or a manual price. Sessions track simulated position, cash, equity, and PnL over time. This is paper-only mark-to-market validation and does not place orders.
- `Options`: runs simulation-only payoff replays for long calls, long puts, bull call spreads, bear put spreads, and long straddles against sample, Coinbase, Yahoo Finance, Tradovate, Polygon, or cached underlying candles.
- `Congress`: syncs recent House PTR PDFs and Senate eFD-derived DataDawn/OpenRegs ticker rows into `../congressional-trading/congress_trades.db`, previews stored disclosures, and replays mapped tickers. Senate rows are not faked.

## Current Data Readiness

The app can run backtests and options replays from local sample candles, public Coinbase crypto candles, public Yahoo Finance stock/ETF candles, and locally cached candles. Congressional disclosure research runs from the local SQLite database after sync.

Credentialed providers still require valid account details before they can pass the full source check:

- E*TRADE needs consumer key/secret plus a fresh OAuth access token and secret. Access tokens expire and may need reconnecting from the `Live Data` page.
- Tradovate needs real username/password credentials that match the configured demo or live base URL.
- Polygon needs a valid `POLYGON_API_KEY` with aggregate-bar access.

All live-provider wiring is read-only market data and simulation support. The app does not place live trades or submit broker orders.

## Development
- Backend: Python 3.12, Flask
- Frontend: React + Vite + TypeScript
