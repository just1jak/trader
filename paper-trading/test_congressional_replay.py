import importlib.util
import sqlite3
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND = Path(__file__).resolve().parent / "backend"
INGEST = PROJECT_ROOT / "congressional-trading" / "congress_ingest.py"
sys.path.insert(0, str(BACKEND))

from utils import congressional


def load_ingest_module():
    spec = importlib.util.spec_from_file_location("congress_ingest", INGEST)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_test_db(path):
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            create table house_trades (
                id integer primary key autoincrement,
                filing_date text,
                transaction_date text,
                member text,
                district text,
                ticker text,
                asset_description text,
                transaction_type text,
                amount text,
                comment text
            );
            create table senate_trades (
                id integer primary key autoincrement,
                filing_date text,
                transaction_date text,
                member text,
                state text,
                ticker text,
                asset_description text,
                transaction_type text,
                amount text,
                comment text
            );
            """
        )
        connection.execute(
            """
            insert into house_trades
              (filing_date, transaction_date, member, district, ticker, asset_description, transaction_type, amount, comment)
            values ('2024-01-02', '2023-12-29', 'Rep Example', 'CA-01', 'AAPL', 'Apple Inc.', 'Purchase', '$1,001 - $15,000', '')
            """
        )
        connection.execute(
            """
            insert into senate_trades
              (filing_date, transaction_date, member, state, ticker, asset_description, transaction_type, amount, comment)
            values ('2024-01-03', '2023-12-28', 'Sen Example', 'NY', 'MSFT', 'Microsoft Corp.', 'Sale', '$15,001 - $50,000', '')
            """
        )


def fake_market_data(symbol, start_date, end_date, source="yahoo"):
    target = start_date + timedelta(days=5)
    index = pd.date_range(start_date.isoformat(), end_date.isoformat(), freq="D")
    base = 100.0 if symbol == "AAPL" else 200.0
    exit_price = 110.0 if symbol == "AAPL" else 180.0
    closes = [base if timestamp.date() < target else exit_price for timestamp in index]
    return pd.DataFrame({"close": closes}, index=index)


def test_congressional_replay_buy_sell_rules():
    original_db = congressional.DB_PATH
    original_fetch = congressional.fetch_market_data
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "congress.db"
        make_test_db(db_path)
        congressional.DB_PATH = db_path
        congressional.fetch_market_data = fake_market_data
        result = congressional.run_congressional_backtest(
            holding_days=5,
            entry_basis="filing_date",
            purchase_action="long",
            sale_action="short",
            max_trades=10,
        )
    congressional.DB_PATH = original_db
    congressional.fetch_market_data = original_fetch

    assert result["metrics"]["total_trades"] == 2
    assert round(result["metrics"]["total_return"], 6) == 0.2
    assert {trade["action"] for trade in result["trade_details"]} == {"long", "short"}
    assert result["rules"]["entry_basis"] == "filing_date"


def test_congressional_replay_can_ignore_sales():
    original_db = congressional.DB_PATH
    original_fetch = congressional.fetch_market_data
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "congress.db"
        make_test_db(db_path)
        congressional.DB_PATH = db_path
        congressional.fetch_market_data = fake_market_data
        result = congressional.run_congressional_backtest(
            holding_days=5,
            purchase_action="long",
            sale_action="ignore",
            max_trades=10,
        )
    congressional.DB_PATH = original_db
    congressional.fetch_market_data = original_fetch

    assert result["metrics"]["total_trades"] == 1
    assert result["metrics"]["attempted_trades"] == 1
    assert result["trade_details"][0]["ticker"] == "AAPL"


def test_ingest_window_and_limit_helpers():
    ingest = load_ingest_module()

    assert ingest._year_window(year=2024) == (2024, 2024)
    assert ingest._year_window(start_year=2021, end_year=2023) == (2021, 2023)
    assert ingest._normalize_limit(0) is None
    assert ingest._normalize_limit(None, all_history=True) is None
    assert ingest._datadawn_rows_from_payload({"columns": ["ticker"], "rows": [["AAPL"]]}) == [{"ticker": "AAPL"}]


def test_house_datadawn_insert_and_pdf_stock_filter():
    ingest = load_ingest_module()
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "congress.db"
        ingest.ensure_schema(db_path)
        with sqlite3.connect(db_path) as connection:
            inserted = ingest._insert_house_datadawn_trade(connection, {
                "id": 42,
                "member_name": "Rep Example",
                "transaction_date": "2024-01-02",
                "disclosure_date": "2024-01-05",
                "ticker": "AAPL",
                "asset_description": "Apple Inc. (AAPL) [ST]",
                "transaction_type": "Purchase",
                "amount_range": "$1,001 - $15,000",
                "owner": "Self",
                "source_url": "https://example.test/ptr.pdf",
                "state_district": "CA01",
                "doc_id": "20000001",
            })
            row = connection.execute("select member, district, ticker, transaction_type from house_trades").fetchone()

    assert inserted == 1
    assert row == ("Rep Example", "CA01", "AAPL", "Purchase")

    trades = ingest.parse_house_ptr_text(
        "Apple Inc. (AAPL) [ST] P 01/02/202401/03/2024$1,001 - $15,000\n"
        "REOF XXVI, LLC [AB] P 01/02/202401/03/2024$250,001 - $500,000"
    )
    assert [trade["ticker"] for trade in trades] == ["AAPL"]


if __name__ == "__main__":
    test_congressional_replay_buy_sell_rules()
    test_congressional_replay_can_ignore_sales()
    test_ingest_window_and_limit_helpers()
    test_house_datadawn_insert_and_pdf_stock_filter()
    print("Congressional replay tests passed")
