# Congressional Trading Strategy

Scrapes disclosed House and Senate stock trades (STOP Act) and maps them to correlated futures for backtesting.

## Data Sources
- House: https://house.gov/stock-watcher-data/xml/ (or JSON endpoint)
- Senate: https://senate.gov/stockwatcher/ (XML/JSON)

## Implementation
- `scrape_house.py`: fetches and parses House disclosures
- `scrape_senate.py`: fetches and parses Senate disclosures
- `backtest.py`: loads trades, maps to futures, simulates returns
- `requirements.txt`: dependencies

## Usage
1. Install dependencies: `pip install -r requirements.txt`
2. Run scrapers to collect data: `python scrape_house.py` and `python scrape_senate.py`
3. Run backtest: `python backtest.py`

Output includes trade log and performance metrics.