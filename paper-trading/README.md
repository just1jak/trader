# Paper Trading Web App

A Flask + React application for backtesting and paper trading futures strategies, initially focused on Tradovate data.

## Features
- Backtesting engine with pluggable strategies
- Historical data fetch from Tradovate (configurable)
- Read-only E*TRADE quote and options-chain API layer
- Settings page for E*TRADE, Tradovate, and reserved Polygon provider credentials
- Live Data page for E*TRADE OAuth connect, live quote fetch, and snapshot collection
- Paper Trade page for forward paper validation with live quote marks or manual prices
- Options page for long call/put, spread, and straddle payoff simulations
- Congress page for local congressional disclosure replay
- React UI for configuring and visualizing backtests
- Dockerized for easy deployment

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Tradovate API credentials (or use CSV fallback)

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

Supported settings today:

- E*TRADE OAuth market-data credentials for quotes, expirations, and option chains.
- Tradovate credentials for historical futures candles.
- Polygon API key storage only; Polygon is not wired into backtests yet.

Docker compose mounts `.env` into the backend container so Settings changes persist across rebuilds.

## Live Data And Strategy Modules

- `Live Data`: save E*TRADE consumer credentials in `Settings`, click `Connect E*TRADE`, paste the verifier code, then fetch or collect quote snapshots. Collected snapshots are stored in `data/market_data.sqlite`.
- `Paper Trade`: create a forward paper session, then mark it from an E*TRADE live quote or a manual price. Sessions track simulated position, cash, equity, and PnL over time. This is paper-only mark-to-market validation and does not place orders.
- `Options`: runs simulation-only payoff replays for long calls, long puts, bull call spreads, bear put spreads, and long straddles against sample or Tradovate underlying candles.
- `Congress`: reads `../congressional-trading/congress_trades.db` and replays stored disclosures. The checked database currently needs scraper-populated rows before results will be meaningful.

## Development
- Backend: Python 3.12, Flask
- Frontend: React + Vite + TypeScript
