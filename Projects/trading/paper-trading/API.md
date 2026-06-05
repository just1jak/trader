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
  - Simulation-only long call/put payoff proxy using underlying OHLCV.
  - Required fields: `symbol`, `from`, `to`, `option_type`, `strike`, `premium`.
  - Optional fields: `timeframe`, `source`, `contracts`, `multiplier`.
  - This does not model historical option bid/ask, implied volatility, theta decay, early exercise, assignment, liquidity, or slippage.
