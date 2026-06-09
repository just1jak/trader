# Next Steps for Congressional Trading Module

## Completed
- House PTR ingestion and Senate eFD-derived ingestion without placeholder rows.
- Backtester that maps stock tickers to futures proxies and calculates returns.
- Flask web app (`web/app.py`) with endpoints to trigger scrape+backtest and return results.
- Database schema (`db_schema.sql`) for persisting trades and backtest results.

## To Do
1. **Install sqlite3 command line tool** (or use Python's sqlite3 module) to initialize the database.
   ```bash
   sudo apt-get install -y sqlite3
   ```
   Then run:
   ```bash
   cd /mnt/shared/knowledge-base/Projects/congressional-trading
   sqlite3 congress_trades.db < db_schema.sql
   ```

2. **Expand persistence and replay coverage**:
   - Keep improving `scrape_house.py` and `scrape_senate.py` coverage for edge-case filings and scanned reports.
   - Modify `backtest.py` to insert a row into `backtest_results` and related details into `backtest_trade_details`.

3. **Enrich data sources**:
   - Current sources:
     - House: official Clerk ZIP/PDF disclosures.
     - Senate: current DataDawn/OpenRegs eFD-derived ticker rows with original PTR links.
   - Add deeper official Senate eFD parsing when the live POST endpoint is accessible to server-side requests.

4. **Improve ticker→futures mapping**:
   - Build a more comprehensive mapping (maybe using sector ETFs or a model).
   - Allow configuration via a CSV or JSON file.

5. **Web UI**:
   - Create a simple HTML template in `web/templates/index.html` with two tabs:
     - "Futures Trading" (placeholder linking to your existing futures‑trader UI)
     - "Congress Trades" (shows latest scraped trades and backtest performance).
   - Use JavaScript to call `/run_analysis` and update the tab without reload.

6. **Dockerization (optional)**:
   - Write a Dockerfile for the Flask app and dependencies.
   - Add to docker‑compose if you want to run alongside the paper‑trading service.

7. **Testing & Validation**:
   - Run the scrapers against real endpoints (if accessible) and verify data.
   - Run backtests over multiple holding periods (1 day, 5 days, etc.) and compare to buy‑and‑hold.

## Example Commands to Initialize & Run
```bash
# Install system deps (if needed)
sudo apt-get update
sudo apt-get install -y python3-pip sqlite3

# Install Python deps
cd /mnt/shared/knowledge-base/Projects/congressional-trading
pip3 install flask

# Init DB
sqlite3 congress_trades.db < db_schema.sql

# Start Flask
cd web
python3 app.py
```

After that, visiting `http://localhost:5001` will show the Congress Trades tab (you’ll need to adapt the template to your UI).

Let me know if you’d like me to generate the actual HTML template, update the scrapers with real parsing, or draft the Dockerfile.
