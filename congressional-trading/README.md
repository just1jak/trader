# Congressional Trading Strategy

Imports disclosed congressional stock trades and maps them to correlated futures for backtesting.

## Data Sources
- House index ZIP: `https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.ZIP`
- House PTR PDFs: `https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{DocID}.pdf`
- Senate eFD: not yet parsed here. The scraper does not create synthetic Senate rows.

## Implementation
- `congress_ingest.py`: downloads official House PTR reports, extracts PDF text with `pypdf`, parses ticker transactions, and inserts rows into SQLite.
- `scrape_house.py`: command-line wrapper for House ingestion.
- `scrape_senate.py`: reports Senate status without inserting placeholder rows.
- `backtest.py`: loads trades, maps to futures, simulates returns
- `requirements.txt`: dependencies

## Usage
1. Install dependencies: `pip install -r requirements.txt`
2. Run House ingestion: `python scrape_house.py --year 2026 --limit 25`
3. Run backtest: `python backtest.py`

Output includes trade log and performance metrics.
