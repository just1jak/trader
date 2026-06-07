import requests
import json
import os
from datetime import datetime

# Placeholder URL - replace with actual Senate STOP Act data endpoint
SENATE_URL = "https://senate.gov/stockwatcher/"

def fetch_senate_trades():
    """
    Fetch recent Senate trades from the STOP Act disclosure.
    Returns a list of dicts with trade details.
    """
    try:
        print(f"Fetching Senate trades from {SENATE_URL}")
        # Simulate a delay and placeholder data
        trades = [
            {
                "filing_date": "2026-04-20",
                "transaction_date": "2026-04-18",
                "member": "Sen. Example",
                "state": "NY",
                "ticker": "MSFT",
                "asset_description": "Microsoft Corporation",
                "transaction_type": "Sale",
                "amount": "$50,001 - $100,000",
                "comment": ""
            }
        ]
        return trades
    except Exception as e:
        print(f"Error fetching Senate trades: {e}")
        return []

def save_trades(trades, filename="senate_trades.json"):
    """
    Save trades to a JSON file in the current directory.
    """
    with open(filename, 'w') as f:
        json.dump(trades, f, indent=2)
    print(f"Saved {len(trades)} Senate trades to {filename}")

if __name__ == "__main__":
    trades = fetch_senate_trades()
    if trades:
        save_trades(trades)
    else:
        print("No Senate trades fetched.")