CREATE TABLE IF NOT EXISTS house_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_date TEXT,
    transaction_date TEXT,
    member TEXT,
    district TEXT,
    ticker TEXT,
    asset_description TEXT,
    transaction_type TEXT,
    amount TEXT,
    comment TEXT,
    UNIQUE(filing_date, transaction_date, member, ticker, transaction_type)
);

CREATE TABLE IF NOT EXISTS senate_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_date TEXT,
    transaction_date TEXT,
    member TEXT,
    state TEXT,
    ticker TEXT,
    asset_description TEXT,
    transaction_type TEXT,
    amount TEXT,
    comment TEXT,
    UNIQUE(filing_date, transaction_date, member, ticker, transaction_type)
);

CREATE TABLE IF NOT EXISTS backtest_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    holding_days INTEGER,
    total_trades INTEGER,
    total_return REAL,
    average_return REAL,
    return_std REAL,
    sharpe_ratio REAL,
    win_rate REAL
);

CREATE TABLE IF NOT EXISTS backtest_trade_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_id INTEGER,
    ticker TEXT,
    transaction_date TEXT,
    member TEXT,
    transaction_type TEXT,
    return REAL,
    FOREIGN KEY(backtest_id) REFERENCES backtest_results(id)
);