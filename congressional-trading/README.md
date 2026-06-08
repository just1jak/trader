# Congressional Trading Strategy

Imports disclosed congressional stock trades and maps them to correlated futures for backtesting.

## Data Sources
- House index ZIP: `https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.ZIP`
- House PTR PDFs: `https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{DocID}.pdf`
- Senate eFD: imports current DataDawn/OpenRegs ticker rows derived from eFD filings, preserving original PTR links. A historical GitHub archive is used only if DataDawn is unavailable. The scraper does not create synthetic Senate rows.

## Implementation
- `congress_ingest.py`: downloads official House PTR reports, extracts PDF text with `pypdf`, parses ticker transactions, imports current Senate eFD-derived rows, and inserts rows into SQLite.
- `scrape_house.py`: command-line wrapper for House ingestion.
- `scrape_senate.py`: command-line wrapper for Senate ingestion.
- `backtest.py`: loads trades, maps to futures, simulates returns
- `requirements.txt`: dependencies

## Usage
1. Install dependencies: `pip install -r requirements.txt`
2. Run House ingestion: `python scrape_house.py --year 2026 --limit 25`
3. Run Senate ingestion: `python scrape_senate.py`
4. Run backtest: `python backtest.py`

Output includes trade log and performance metrics.
