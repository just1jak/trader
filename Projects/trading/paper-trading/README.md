# Paper Trading Web App

A Flask + React application for backtesting and paper trading futures strategies, initially focused on Tradovata data.

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

## Development
- Backend: Python 3.12, Flask
- Frontend: React + Vite + TypeScript
