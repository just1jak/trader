# Trading Project Notes

Scope: this file applies to `Projects/trading` and its children.

## Project Shape

- `README.md` is the umbrella note for the trading workspace.
- `paper-trading/` is a Flask + Flask-RESTX backend with a React + Vite frontend for futures backtesting and paper-trading validation.
- `congressional-trading/` is a congressional disclosure research/backtesting area with placeholder House/Senate scrapers, a deterministic futures-data backtest, and a checked-in SQLite database.

## Current Intent

- Treat this repo as research and simulation first. Do not add live trading or order execution without explicit user approval and clear risk controls.
- Prioritize paper-trading validation, backtest correctness, and data-source reliability before any automation that could affect real capital.
- Keep findings grounded in the code and data present here; several docs describe intended behavior that is not fully implemented yet.

## Paper Trading

- Backend entrypoint: `paper-trading/backend/app.py`.
- Backend API namespace: `POST /api/v1/backtest`.
- Strategy modules live in `paper-trading/backend/api/strategies/` and must expose `generate_signals(data, params)`.
- Backtest utility: `paper-trading/backend/utils/backtest.py`.
- Tradovate client: `paper-trading/backend/utils/tradovate.py`; it authenticates during client construction and requires env credentials.
- Frontend entrypoint: `paper-trading/frontend/src/App.tsx`.
- Frontend API helper: `paper-trading/frontend/src/hooks/useApi.ts`.
- Docker compose file: `paper-trading/docker-compose.yml`.
- Typical container run: from `paper-trading/`, use `docker compose up --build`.

Known drift and hotspots:

- The frontend calls `/backtest`, while the backend mounts `/api/v1/backtest`; wire the Vite backend URL/base path before expecting the UI to work against Flask.
- `docker-compose.yml` sets `VITE_BACKEND_URL=http://localhost:5000`, but the current `useApi` hook does not read it.
- `App.tsx` offers a `vwap_mr` strategy option, but no `vwap_mr.py` strategy exists.
- `volume_profile_orderflow.py` exists and has a test script, but it is not currently exposed in the UI strategy selector.
- Verify the backend package/import layout before running: `app.py` imports `api.routes`, while `routes.py` uses relative imports into `..utils`.

## Congressional Trading

- Main docs: `congressional-trading/README.md`, `congressional-trading/NEXT_STEPS.md`, and `congressional-trading/memory.md`.
- Scrapers: `scrape_house.py` and `scrape_senate.py`.
- Backtest: `backtest.py`.
- The scrapers currently return placeholder example trades rather than parsing the live official disclosure feeds.
- The backtest currently uses deterministic synthetic futures data via `fetch_futures_data`, not a live market-data source.

Known drift and hotspots:

- Root `README.md` references `congressional/congress_trades.db`; the actual path is `congressional-trading/congress_trades.db`.
- Official disclosure endpoints and data formats may change; verify them live before relying on scraper assumptions.

## Hygiene

- `paper-trading/.env` is currently tracked. Do not print it or copy its contents into chat. If it contains real credentials, rotate them and untrack the file in a dedicated cleanup.
- A Python bytecode file under `paper-trading/backend/api/strategies/__pycache__/` is also tracked. Leave it alone unless doing an explicit repo hygiene pass.
- There is no `.gitignore` in this folder as of the init pass.

## Verification Notes

- For Python syntax-only checks, prefer `python3 -m py_compile ...` on touched files.
- For strategy behavior, `paper-trading/test_volume_profile.py` exercises `volume_profile_orderflow.py` with generated data.
- Frontend build uses `npm run build` from `paper-trading/frontend/`; there is no lockfile in the frontend folder as of the init pass.
