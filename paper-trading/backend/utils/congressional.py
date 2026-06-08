import datetime
import sqlite3
import statistics
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / 'congressional-trading' / 'congress_trades.db'

TICKER_TO_FUTURES = {
    'AAPL': 'ES=F',
    'MSFT': 'ES=F',
    'GOOGL': 'ES=F',
    'GOOG': 'ES=F',
    'AMZN': 'ES=F',
    'META': 'ES=F',
    'NVDA': 'NQ=F',
    'TSLA': 'NQ=F',
    'XOM': 'CL=F',
    'CVX': 'CL=F',
    'GLD': 'GC=F',
    'SLV': 'SI=F',
}


def list_congressional_trades(limit=50):
    if not DB_PATH.exists():
        return {'trades': [], 'total': 0, 'database': str(DB_PATH)}

    limit = max(1, min(int(limit or 50), 250))
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            select chamber, filing_date, transaction_date, member, region, ticker,
                   asset_description, transaction_type, amount, comment
            from (
              select 'House' as chamber, filing_date, transaction_date, member,
                     district as region, ticker, asset_description, transaction_type,
                     amount, comment
              from house_trades
              union all
              select 'Senate' as chamber, filing_date, transaction_date, member,
                     state as region, ticker, asset_description, transaction_type,
                     amount, comment
              from senate_trades
            )
            order by filing_date desc, transaction_date desc
            limit ?
            """,
            (limit,),
        ).fetchall()
        total = connection.execute(
            """
            select
              (select count(*) from house_trades) +
              (select count(*) from senate_trades)
            """
        ).fetchone()[0]
    return {'trades': [_row_to_dict(row) for row in rows], 'total': total, 'database': str(DB_PATH)}


def run_congressional_backtest(holding_days=5):
    trades = list_congressional_trades(limit=250)['trades']
    holding_days = max(1, min(int(holding_days or 5), 60))
    if not trades:
        return {
            'metrics': _empty_metrics(),
            'trade_details': [],
            'holding_days': holding_days,
            'message': 'No congressional trades are stored yet. Run the House/Senate scrapers before this backtest can produce results.',
        }

    returns = []
    details = []
    for trade in trades:
        trade_return = calculate_trade_return(trade, holding_days=holding_days)
        if trade_return is None:
            continue
        returns.append(trade_return)
        details.append({
            'ticker': trade.get('ticker'),
            'member': trade.get('member'),
            'chamber': trade.get('chamber'),
            'transaction_date': trade.get('transaction_date'),
            'transaction_type': trade.get('transaction_type'),
            'futures_symbol': get_futures_symbol(trade.get('ticker')),
            'return': trade_return,
        })

    if not returns:
        return {
            'metrics': _empty_metrics(),
            'trade_details': [],
            'holding_days': holding_days,
            'message': 'Trades exist, but none could be mapped to the current futures proxy table.',
        }

    average_return = statistics.mean(returns)
    return_std = statistics.stdev(returns) if len(returns) > 1 else 0
    sharpe_ratio = average_return / return_std if return_std else 0
    win_rate = sum(1 for value in returns if value > 0) / len(returns)
    return {
        'metrics': {
            'total_trades': len(returns),
            'total_return': sum(returns),
            'average_return': average_return,
            'return_std': return_std,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
        },
        'trade_details': details,
        'holding_days': holding_days,
        'message': 'Congressional disclosure replay uses deterministic futures proxy data until live market history is wired.',
    }


def calculate_trade_return(trade, holding_days=5):
    ticker = trade.get('ticker')
    futures_symbol = get_futures_symbol(ticker)
    if not futures_symbol:
        return None

    try:
        transaction_date = datetime.datetime.strptime(trade['transaction_date'], '%Y-%m-%d')
    except (KeyError, TypeError, ValueError):
        return None
    if transaction_date.date() > datetime.datetime.utcnow().date():
        return None

    start_date = transaction_date.strftime('%Y-%m-%d')
    end_date = (transaction_date + datetime.timedelta(days=holding_days)).strftime('%Y-%m-%d')
    data = fetch_futures_data(futures_symbol, start_date, end_date)
    if not data:
        return None

    entry_price = data[0]['close']
    exit_price = data[-1]['close']
    transaction_type = (trade.get('transaction_type') or '').lower()
    if 'sale' in transaction_type:
        return (entry_price - exit_price) / entry_price
    return (exit_price - entry_price) / entry_price


def get_futures_symbol(ticker):
    return TICKER_TO_FUTURES.get((ticker or '').upper())


def fetch_futures_data(symbol, start_date, end_date):
    try:
        start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return []

    if end < start:
        end = start

    base_price = 4000
    if 'NQ' in symbol:
        base_price = 18000
    elif 'CL' in symbol:
        base_price = 80
    elif 'GC' in symbol:
        base_price = 2000
    elif 'SI' in symbol:
        base_price = 25

    data = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            seed = sum(ord(char) for char in f'{symbol}{current:%Y-%m-%d}')
            variation = (seed % 200) - 100
            close_price = base_price + variation
            data.append({'date': current.strftime('%Y-%m-%d'), 'close': close_price})
        current += datetime.timedelta(days=1)
    return data


def _row_to_dict(row):
    return {key: row[key] for key in row.keys()}


def _empty_metrics():
    return {
        'total_trades': 0,
        'total_return': 0,
        'average_return': 0,
        'return_std': 0,
        'sharpe_ratio': 0,
        'win_rate': 0,
    }
