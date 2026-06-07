# Paper Trading API Wiring

All routes are mounted under `/api/v1`.

## Backtesting

- `POST /backtest`
  - Runs an existing strategy module against OHLCV candles.
  - `source=sample` uses `data/sample_ES_1min.csv`.
  - `source=tradovate` uses the existing Tradovate client.
  - `source=etrade` is intentionally not supported for historical candles because the wired E*TRADE layer exposes quote and option-chain snapshots, not historical OHLCV bars.

- `GET /market/backtest-data`
  - Returns candles for inspection before a run.
  - Query params: `symbol`, `timeframe`, `from`, `to`, `source`.

## Provider Settings

- `GET /settings/providers`
  - Returns supported providers, configured/missing status, and masked secret values.
  - The browser never receives raw secret values.

- `POST /settings/providers/{provider_key}`
  - Saves provider settings to the backend `.env` file.
  - Body shape: `{ "values": { "ENV_KEY": "value" } }`.
  - Supported provider keys: `etrade`, `tradovate`, `polygon`.
  - Blank submitted fields are ignored, so a blank saved secret input keeps the existing value.

## E*TRADE Market Data

The E*TRADE layer is read-only. It does not place, preview, modify, or cancel orders.

Required env vars:

```text
ETRADE_ENV=sandbox
ETRADE_CONSUMER_KEY=...
ETRADE_CONSUMER_SECRET=...
ETRADE_ACCESS_TOKEN=...
ETRADE_ACCESS_TOKEN_SECRET=...
```

Routes:

- `POST /etrade/oauth/start`
  - Requests an E*TRADE OAuth request token and returns an authorization URL.

- `POST /etrade/oauth/complete`
  - Body shape: `{ "verifier": "..." }`.
  - Exchanges the verifier code for an access token and access token secret, then saves them server-side.

- `POST /etrade/oauth/renew`
  - Renews the access token when E*TRADE accepts renewal.

- `GET /etrade/live/quote?symbols=AAPL,SPY&detailFlag=ALL`
  - Fetches a live read-only quote snapshot.

- `POST /etrade/live/collect`
  - Body shape: `{ "symbols": "AAPL,SPY", "detailFlag": "ALL" }`.
  - Fetches and stores one quote snapshot in `data/market_data.sqlite`.

- `GET /etrade/live/snapshots`
  - Lists saved quote snapshot metadata.

- `GET /market/quote/{symbols}`
  - Calls E*TRADE quote data for one or more comma-separated equity or option symbols.
  - Optional query: `detailFlag=ALL|FUNDAMENTAL|INTRADAY|OPTIONS|WEEK_52|MF_DETAIL`.

- `GET /market/options/expirations/{symbol}`
  - Calls E*TRADE option expiration dates.
  - Optional query: `expiryType=ALL|WEEKLY|MONTHLY|...`.

- `GET /market/options/chain/{symbol}`
  - Calls E*TRADE option chains.
  - Optional query params include `expiryYear`, `expiryMonth`, `expiryDay`, `strikePriceNear`, `noOfStrikes`, `chainType`, `includeWeekly`, `skipAdjusted`, `optionCategory`, and `priceType`.

## Options Simulation

- `POST /options/backtest`
  - Simulation-only options payoff proxy using underlying OHLCV.
  - Required fields: `symbol`, `from`, `to`, `option_type`, `strike`, `premium`.
  - Optional fields: `timeframe`, `source`, `contracts`, `multiplier`, `strategy`, `short_strike`, `short_premium`.
  - Supported strategies: `long_call`, `long_put`, `bull_call_spread`, `bear_put_spread`, `long_straddle`.
  - This does not model historical option bid/ask, implied volatility, theta decay, early exercise, assignment, liquidity, or slippage.

## Congressional Replay

- `GET /congress/trades`
  - Lists locally stored House/Senate disclosure rows from `congressional-trading/congress_trades.db`.

- `POST /congress/backtest`
  - Body shape: `{ "holding_days": 5 }`.
  - Replays locally stored disclosures against deterministic futures proxies.
  - Returns zero-trade metrics when the SQLite disclosure tables are empty.
