# Next Steps for Congressional Trading Module

## Completed
- Scrapers for House and Senate trades (placeholder data).
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

2. **Update scrapers and backtester to persist to SQLite**:
   - Modify `scrape_house.py` and `scrape_senate.py` to insert rows into `house_trades` and `senate_trades` (using INSERT OR IGNORE to avoid duplicates).
   - Modify `backtest.py` to insert a row into `backtest_results` and related details into `backtest_trade_details`.

3. **Enrich data sources**:
   - Replace placeholder URLs with actual STOP Act data endpoints:
     - House: https://house.gov/stock-watcher-data/xml/ (or JSON)
     - Senate: https://senate.gov/stockwatcher/ (XML/JSON)
   - Implement proper parsing (XML/JSON) and handle pagination to capture multiple years.

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