# Paper Trading Web App

A Flask + React application for backtesting and paper trading futures strategies, initially focused on Tradovate data.

## Features
- Backtesting engine with pluggable strategies
- Historical data fetch from Tradovate (configurable)
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

## Development
- Backend: Python 3.12, Flask
- Frontend: React + Vite + TypeScript
