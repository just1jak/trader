# Paper Trading Web App

A Flask + React application for backtesting and paper trading futures strategies, initially focused on Tradovate data.

## Features
- Backtesting engine with pluggable strategies
- Historical data fetch from Tradovate (configurable)
- Read-only E*TRADE quote and options-chain API layer
- Settings page for E*TRADE, Tradovate, and reserved Polygon provider credentials
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

## Development
- Backend: Python 3.12, Flask
- Frontend: React + Vite + TypeScript
