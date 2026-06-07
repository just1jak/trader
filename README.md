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
- Tradovate historical futures data path
- Read-only E*TRADE quote and options-chain API layer
- E*TRADE OAuth connect flow and snapshot collection store
- Simulation-only options strategy payoff backtester
- Congressional disclosure replay endpoint

## Key Files

- `congressional-trading/congress_trades.db` — congressional trade database
- `congressional-trading/backtest.py` — congressional-to-futures backtest prototype
- `paper-trading/` — simulation backend + UI
- `paper-trading/API.md` — detailed API wiring notes
- `paper-trading/data/sample_ES_1min.csv` — local sample ES candles
- `paper-trading/backend/api/routes.py` — Flask API routes
- `paper-trading/backend/utils/etrade.py` — read-only E*TRADE OAuth market client
- `paper-trading/backend/utils/backtest_data.py` — sample/Tradovate candle loading
- `paper-trading/backend/utils/options_backtest.py` — options payoff simulation
- `paper-trading/frontend/src/App.tsx` — paper-trading dashboard

## Paper-Trading API

All paper-trading API routes are mounted under `/api/v1`.

### Backtesting

- `POST /api/v1/backtest`
  - Runs one of the existing strategy modules against OHLCV candles.
  - `source=sample` uses `paper-trading/data/sample_ES_1min.csv`.
  - `source=tradovate` uses the existing Tradovate client.
  - `source=etrade` is intentionally not supported for historical candles because the wired E*TRADE layer exposes quote and option-chain snapshots, not historical OHLCV bars.

- `GET /api/v1/market/backtest-data`
  - Returns candles for inspection before a run.
  - Query params: `symbol`, `timeframe`, `from`, `to`, `source`.

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

- `POST /api/v1/congress/backtest`
  - Runs the congressional disclosure replay against deterministic futures proxies.
  - Required data caveat: the checked database exists, but it must contain scraped disclosure rows before the replay can produce trades.

## Frontend Wiring

The React dashboard posts to `POST /api/v1/backtest` and includes a data-source selector:

- `Sample CSV` — uses the local ES sample data and works without broker credentials.
- `Tradovate` — uses the existing Tradovate historical-data client when credentials are configured.

The dashboard also includes a `Settings` module for broker and market-data credentials:

- E*TRADE stores read-only OAuth market-data credentials for quote, expiration, and option-chain routes.
- Tradovate stores historical futures data credentials used by backtests.
- Polygon is reserved as a stored provider slot, but it is not used by backtests yet.
- Secret fields are masked when read back by the browser. Leaving a saved secret field blank keeps the existing value.

Additional dashboard modules:

- `Live Data` — E*TRADE OAuth connect, quote fetch, quote collection, and saved snapshot list.
- `Options` — simulation-only options payoff strategy replay.
- `Congress` — local congressional disclosure replay and stored disclosure preview.

The Vite dev server proxies `/api` to `http://localhost:5001`, and the frontend also defaults to `http://localhost:5001` during dev when `VITE_BACKEND_URL` is not set. If macOS has another service on port `5000`, use the alternate backend port path:

```bash
cd paper-trading/backend
PORT=5001 python3 app.py

cd ../frontend
npm run dev
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
BACKEND_PORT=5000
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
curl http://localhost:${BACKEND_PORT:-5000}/api/v1/market/backtest-data?symbol=ES\&source=sample\&timeframe=1min\&from=2025-01-02\&to=2025-01-02
```

7. Open the frontend:

```text
http://your-server-host:${FRONTEND_PORT:-80}
```

The production frontend is served by nginx. Browser requests to `/api/` are proxied to the backend container, so `VITE_BACKEND_URL` should stay empty for this production compose setup.

## Current Verification Notes

- Backend syntax checks pass with `python3 -m py_compile` when `PYTHONPYCACHEPREFIX` points to a writable temp directory.
- Local sample candle loading and the options payoff simulation have been smoke-tested.
- Frontend build has been verified with `npm run build`; the generated `dist/` folder is ignored for source control.

## External API References

- [E*TRADE Getting Started](https://developer.etrade.com/getting-started)
- [E*TRADE OAuth Developer Guide](https://developer.etrade.com/getting-started/developer-guides)
- [E*TRADE Market Option Chains API](https://apisb.etrade.com/docs/api/market/api-market-v1.html)
- [E*TRADE Quote API](https://apisb.etrade.com/docs/api/market/api-quote-v1.html)
