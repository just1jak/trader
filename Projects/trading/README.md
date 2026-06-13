# Trading: Congressional, Options, Crypto, Futures

Consolidated trading research, strategy validation, and simulation workspace.

This workspace is currently wired for read-only market data and paper/backtest
workflows. Live order execution is intentionally not wired here.

## Current Projects

- **congressional-trading** — house/senate trade tracking + backtesting
- **paper-trading** — Flask + React pre-live simulation environment

## Roadmap

1. **Paper-trading validation** — confirm strategies in paper market (no real capital)
2. **LLM feedback loop** — train bot using market signals + news
3. **Options/crypto scalping** — add new instruments to strategy set
4. **Futures integration** — add leverage strategies
5. **Live bot deployment** — automated trading with proper risk controls

## Tech

- Python scrapers and congressional trade backtester
- Flask + Flask-RESTX paper-trading API
- React + Vite dashboard frontend
- Local OHLCV sample data for credential-free backtests
- Public no-key Coinbase crypto OHLCV candle path
- Public no-key Yahoo Finance stock/ETF OHLCV candle path
- Tradovate historical futures data path
- Polygon historical stock aggregate data path
- Read-only E*TRADE quote and options-chain API layer
- E*TRADE OAuth connect flow and snapshot collection store
- Data-source diagnostics and full source smoke-test API/dashboard page
- Local OHLCV candle cache with collect/replay routes
- Forward paper-trading sessions marked from live quotes or manual prices
- Simulation-only options strategy payoff backtester
- Official House PTR disclosure importer, Senate eFD-derived importer, and congressional replay endpoint

## Key Files

- `congressional-trading/congress_trades.db` — congressional trade database
- `congressional-trading/congress_ingest.py` — House PTR ZIP/PDF importer plus Senate eFD-derived fallback importer
- `congressional-trading/backtest.py` — congressional-to-futures backtest prototype
- `paper-trading/` — simulation backend + UI
- `paper-trading/API.md` — detailed API wiring notes
- `paper-trading/data/sample_ES_1min.csv` — local sample ES candles
- `paper-trading/data/market_data.sqlite` — local E*TRADE quote snapshots and OHLCV candle cache
- `paper-trading/backend/utils/candle_cache.py` — local OHLCV candle cache
- `paper-trading/backend/api/routes.py` — Flask API routes
- `paper-trading/backend/utils/etrade.py` — read-only E*TRADE OAuth market client
- `paper-trading/backend/utils/etrade_collection.py` — E*TRADE quote snapshot storage and summaries
- `paper-trading/backend/utils/coinbase.py` — public crypto OHLCV candle client
- `paper-trading/backend/utils/yahoo.py` — public stock/ETF OHLCV candle client
- `paper-trading/backend/utils/polygon.py` — Polygon historical aggregate client
- `paper-trading/backend/utils/backtest_data.py` — local sample candle loading
- `paper-trading/backend/utils/options_backtest.py` — options payoff simulation
- `paper-trading/frontend/src/App.tsx` — paper-trading dashboard

## Paper-Trading API

All paper-trading API routes are mounted under `/api/v1`.

### Backtesting

- `POST /api/v1/backtest`
  - Runs one of the existing strategy modules against OHLCV candles.
  - `source=sample` uses `paper-trading/data/sample_ES_1min.csv`.
  - `source=coinbase` uses public no-key Coinbase crypto OHLCV candles for products such as `BTC-USD` and `ETH-USD`.
  - `source=yahoo` uses public no-key Yahoo Finance stock/ETF candles for symbols such as `AAPL`, `SPY`, and `QQQ`.
  - `source=tradovate` uses the existing Tradovate client.
  - `source=polygon` uses Polygon aggregate bars for stock symbols such as `AAPL`, `SPY`, and `QQQ`.
  - `source=cache` replays previously collected OHLCV bars from `paper-trading/data/market_data.sqlite`.
  - `source=etrade` is intentionally not supported for historical candles because the wired E*TRADE layer exposes quote and option-chain snapshots, not historical OHLCV bars.

- `GET /api/v1/market/backtest-data`
  - Returns candles for inspection before a run.
  - Query params: `symbol`, `timeframe`, `from`, `to`, `source`.

- `POST /api/v1/market/candles/collect`
  - Fetches candles from `sample`, `coinbase`, `yahoo`, `tradovate`, or `polygon` and stores them in the local candle cache.
  - Body shape: `{ "source": "yahoo", "symbol": "AAPL", "timeframe": "1d", "from": "2025-01-02", "to": "2025-01-31" }`.

- `GET /api/v1/market/candles/cache`
  - Lists cached candle datasets and row counts.

- `GET /api/v1/market/candles/cache/preview`
  - Returns a limited row preview for one cached dataset so the frontend can show the actual stored OHLCV rows.

### Data Source Diagnostics

- `GET /api/v1/data/sources`
  - Returns configured status, row counts, and a preview/error for each source.
  - Add `?probe=true` to make a lightweight test request against configured external providers.
  - Current source keys: `sample`, `coinbase`, `yahoo`, `tradovate`, `etrade_market_data`, `polygon`, `cache`, and `congress`.
  - This route is the fastest way to confirm whether the dashboard has real usable data before trusting a backtest.

- `GET /api/v1/data/smoke-test`
  - Runs a read-only full source check across sample CSV, Coinbase, Yahoo Finance, cache replay, congressional disclosures, E*TRADE, Tradovate, and Polygon.
  - Returns `pass`, `warning`, `blocked`, or `fail` per source plus a summary of blocked or failed providers.
  - E*TRADE, Tradovate, and Polygon report `blocked` until valid credentials are saved and accepted by those providers.
  - This route verifies source access only. It does not place trades, clear credentials, or write new candle rows.

- `POST /api/v1/data/collect-defaults`
  - Seeds safe starter datasets into local storage: sample ES, Coinbase BTC-USD, Yahoo AAPL, configured Tradovate/Polygon candles, and an E*TRADE AAPL quote snapshot when OAuth is valid.
  - Returns per-source `collected`, `empty`, `blocked`, or `failed` results and leaves public/local sources cached even when credentialed providers are not ready.

### E*TRADE Market Data

The E*TRADE layer is read-only. It can retrieve quote, option-expiration, and option-chain data, but it does not place, preview, modify, or cancel orders.

Required environment variables:

```text
ETRADE_ENV=sandbox
ETRADE_CONSUMER_KEY=...
ETRADE_CONSUMER_SECRET=...
ETRADE_ACCESS_TOKEN=...
ETRADE_ACCESS_TOKEN_SECRET=...
```

Access tokens are created through the dashboard `Live Data` tab:

1. Save `ETRADE_CONSUMER_KEY` and `ETRADE_CONSUMER_SECRET` in `Settings`.
2. Open `Live Data`.
3. Click `Connect E*TRADE`.
4. Approve the app on E*TRADE and paste the verifier code back into the app.
5. Click `Save token`.

The app can then fetch live quote snapshots and save them into `paper-trading/data/market_data.sqlite`.

Routes:

- `POST /api/v1/etrade/oauth/start`
  - Requests a temporary E*TRADE OAuth token and returns the authorization URL.

- `POST /api/v1/etrade/oauth/complete`
  - Exchanges the verifier code for the access token and access token secret.

- `POST /api/v1/etrade/oauth/renew`
  - Renews the access token when E*TRADE allows renewal.

- `GET /api/v1/etrade/live/quote`
  - Fetches a read-only live quote snapshot.
  - Query params: `symbols`, `detailFlag`.

- `POST /api/v1/etrade/live/collect`
  - Fetches and stores a quote snapshot in local SQLite.

- `GET /api/v1/etrade/live/snapshots`
  - Lists stored E*TRADE snapshot metadata.

- `GET /api/v1/paper/sessions`
  - Lists forward paper-trading sessions and their latest equity mark.

- `POST /api/v1/paper/sessions`
  - Creates a paper-only forward validation session.
  - Supported models: `forward_long`, `forward_short`, and `observe_only`.
  - Required fields: `symbol`; optional fields include `name`, `strategy`, `quantity`, `initial_cash`, and `notes`.

- `POST /api/v1/paper/mark`
  - Marks a paper session from a manual price or, when `price` is omitted, the current E*TRADE quote for that session symbol.
  - Saves live quote marks as `paper_quote` snapshots in `paper-trading/data/market_data.sqlite`.
  - This is simulation-only mark-to-market tracking; it does not place or preview orders.

- `GET /api/v1/paper/sessions/{session_id}/marks`
  - Lists the saved equity marks for a forward paper session.

- `GET /api/v1/market/quote/{symbols}`
  - Calls E*TRADE quote data for one or more comma-separated equity or option symbols.
  - Optional query: `detailFlag=ALL|FUNDAMENTAL|INTRADAY|OPTIONS|WEEK_52|MF_DETAIL`.

- `GET /api/v1/market/options/expirations/{symbol}`
  - Calls E*TRADE option expiration dates.
  - Optional query: `expiryType=ALL|WEEKLY|MONTHLY|...`.

- `GET /api/v1/market/options/chain/{symbol}`
  - Calls E*TRADE option chains.
  - Optional query params include `expiryYear`, `expiryMonth`, `expiryDay`, `strikePriceNear`, `noOfStrikes`, `chainType`, `includeWeekly`, `skipAdjusted`, `optionCategory`, and `priceType`.

### Options Simulation

- `POST /api/v1/options/backtest`
  - Simulation-only options payoff proxy using underlying OHLCV.
  - Required fields: `symbol`, `from`, `to`, `option_type`, `strike`, `premium`.
  - Optional fields: `timeframe`, `source`, `contracts`, `multiplier`, `strategy`, `short_strike`, `short_premium`.
  - Supported strategies: `long_call`, `long_put`, `bull_call_spread`, `bear_put_spread`, `long_straddle`.
  - Does not model historical option bid/ask, implied volatility, theta decay, early exercise, assignment, liquidity, or slippage.

### Congressional Replay

- `GET /api/v1/congress/trades`
  - Lists locally stored House/Senate disclosures from `congressional-trading/congress_trades.db`.

- `POST /api/v1/congress/ingest`
  - Downloads the official House disclosure index ZIP, fetches recent PTR PDFs, parses ticker transactions, and stores them in SQLite.
  - When `include_senate=true`, imports recent Senate eFD-derived ticker rows from DataDawn/OpenRegs with original PTR links. The importer does not create synthetic Senate rows.
  - Body shape: `{ "year": 2026, "limit": 25, "include_senate": true }`.

- `POST /api/v1/congress/backtest`
  - Runs the congressional disclosure replay against deterministic futures proxies.
  - Required data caveat: the checked database exists, but it must contain scraped disclosure rows before the replay can produce trades.

## Frontend Wiring

The React dashboard posts to `POST /api/v1/backtest` and includes a data-source selector:

- `Sample CSV` — uses the local ES sample data and works without broker credentials.
- `Coinbase crypto` — uses no-key public Coinbase candles for products such as `BTC-USD` and `ETH-USD`.
- `Yahoo Finance` — uses no-key public stock/ETF candles for symbols such as `AAPL`, `SPY`, and `QQQ`; the endpoint can rate-limit.
- `Tradovate` — uses the existing Tradovate historical-data client when credentials are configured.
- `Polygon` — uses stock aggregate candles when a Polygon API key is configured.
- `Cached candles` — replays OHLCV bars collected through the backtest `Collect candles` action.

The dashboard also includes a `Settings` module for broker and market-data credentials:

- E*TRADE stores read-only OAuth market-data credentials for quote, expiration, and option-chain routes.
- Tradovate stores historical futures data credentials used by backtests. Prefer `TRADOVATE_USERNAME` and `TRADOVATE_PASSWORD`; optional app registration fields are `TRADOVATE_CID` and `TRADOVATE_SECRET`. The older `TRADOVATE_API_KEY` and `TRADOVATE_API_SECRET` names are still supported as username/password fallbacks.
- Polygon stores the API key and optional base URL used by stock candle backtests.
- Secret fields are masked when read back by the browser. Leaving a saved secret field blank keeps the existing value.
- Saved secret fields can be explicitly cleared in Settings, which is useful when an E*TRADE access token expires or a provider key needs to be replaced.

Additional dashboard modules:

- `Live Data` — E*TRADE OAuth connect, quote fetch, quote collection, and saved snapshot list.
- `Data Sources` — source readiness cards, row counts, sample previews, probe errors, the full source-check matrix, default collection, custom source workbench, cached dataset list, and candle-row preview.
- `Backtest` — includes a `Collect candles` action that stores the selected provider/date range into the local cache.
- `Paper Trade` — forward paper sessions, live quote marks, manual test marks, and equity/PnL history.
- `Options` — simulation-only options payoff strategy replay.
- `Congress` — House PTR sync, Senate eFD-derived sync, local congressional disclosure replay, and stored disclosure preview.

The Vite dev server proxies `/api` to `http://localhost:5001` by default, and the frontend also uses `VITE_BACKEND_URL` when explicitly set.
This avoids the common macOS conflict where AirPlay Receiver / Control Center already owns port `5000`. If port `5001` is already taken, use an alternate backend port and point Vite at it:

```bash
cd paper-trading/backend
PORT=5002 python3 app.py

cd ../frontend
VITE_BACKEND_URL=http://localhost:5002 npm run dev
```

Frontend deployment files:

- `paper-trading/frontend/Dockerfile` — dev container for the existing `docker-compose.yml`.
- `paper-trading/frontend/Dockerfile.prod` — production static build image.
- `paper-trading/frontend/nginx.conf` — serves the built app and proxies `/api/` to the backend service.
- `paper-trading/docker-compose.prod.yml` — production-oriented compose file for server deployment.

## Local Development

From `paper-trading/`:

```bash
docker compose up --build
```

Backend:

```bash
cd paper-trading/backend
python3 app.py
```

Frontend:

```bash
cd paper-trading/frontend
npm install
npm run dev
```

## Frontend Build

From `paper-trading/frontend`:

```bash
npm install
npm run build
```

The build output is written to `paper-trading/frontend/dist`.

## Server Deployment

Use the production compose file when deploying the full app to a server.

1. Copy `.env.example` to `.env` inside `paper-trading/`.
2. Fill in broker credentials only for the providers you intend to use.
3. Set optional server ports if needed:

```text
FRONTEND_PORT=80
BACKEND_PORT=5001
```

4. Build and start:

```bash
cd paper-trading
docker compose -f docker-compose.prod.yml up --build -d
```

5. Check running services:

```bash
docker compose -f docker-compose.prod.yml ps
```

6. Check backend health manually from the server:

```bash
curl http://localhost:${BACKEND_PORT:-5001}/api/v1/market/backtest-data?symbol=ES\&source=sample\&timeframe=1min\&from=2025-01-02\&to=2025-01-02
```

7. Open the frontend:

```text
http://your-server-host:${FRONTEND_PORT:-80}
```

The production frontend is served by nginx. Browser requests to `/api/` are proxied to the backend container, so `VITE_BACKEND_URL` should stay empty for this production compose setup.

## Current Verification Notes

- Backend syntax checks pass with `python3 -m py_compile` when `PYTHONPYCACHEPREFIX` points to a writable temp directory.
- Local sample candle loading and the options payoff simulation have been smoke-tested.
- Coinbase public BTC-USD candles have been smoke-tested through preview, collect, cache replay, strategy backtest, and options replay routes.
- Yahoo public AAPL candles have been smoke-tested through preview, collect, cache replay, strategy backtest, and options replay routes.
- E*TRADE quote collection has been smoke-tested against the saved OAuth token; sandbox responses can be historical/canned, and expired tokens return a reconnect message.
- Tradovate and Polygon fail cleanly with JSON setup errors when credentials are missing or rejected.
- The candle cache has been smoke-tested by collecting sample ES candles and replaying a `source=cache` backtest.
- Congressional House ingestion has been verified against the official 2026 Clerk ZIP/PDF path, and Senate ingestion uses current DataDawn/OpenRegs eFD-derived ticker rows with original PTR links when the official eFD AJAX endpoint is unavailable to server-side requests.
- Frontend build has been verified with `npm run build`; the generated `dist/` folder is ignored for source control.

## External API References

- [E*TRADE Getting Started](https://developer.etrade.com/getting-started)
- [E*TRADE OAuth Developer Guide](https://developer.etrade.com/getting-started/developer-guides)
- [E*TRADE Market Option Chains API](https://apisb.etrade.com/docs/api/market/api-market-v1.html)
- [E*TRADE Quote API](https://apisb.etrade.com/docs/api/market/api-quote-v1.html)
- [Coinbase Exchange Get Product Candles](https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductcandles)
