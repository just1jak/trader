import datetime as dt
import math
import re
import sqlite3
import statistics
from pathlib import Path

from utils.yahoo import YahooClient


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / 'congressional-trading' / 'congress_trades.db'

VALID_ACTIONS = {'long', 'short', 'ignore'}
VALID_ENTRY_BASIS = {'filing_date', 'transaction_date'}


def list_congressional_trades(limit=50):
    if not DB_PATH.exists():
        return {'trades': [], 'total': 0, 'database': str(DB_PATH)}

    limit = max(1, min(int(limit or 50), 5000))
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
            order by coalesce(nullif(filing_date, ''), transaction_date) desc, transaction_date desc
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


def run_congressional_backtest(
    holding_days=5,
    entry_basis='filing_date',
    purchase_action='long',
    sale_action='short',
    max_trades=250,
    min_amount=None,
    chambers=None,
    tickers=None,
    source='yahoo',
):
    rules = _normalize_rules(
        holding_days=holding_days,
        entry_basis=entry_basis,
        purchase_action=purchase_action,
        sale_action=sale_action,
        max_trades=max_trades,
        min_amount=min_amount,
        chambers=chambers,
        tickers=tickers,
        source=source,
    )
    stored = list_congressional_trades(limit=5000)
    trades = _filter_trades(stored['trades'], rules)[:rules['max_trades']]
    if not stored['trades']:
        return {
            'metrics': _empty_metrics(),
            'trade_details': [],
            'skipped_details': [],
            'rules': rules,
            'holding_days': rules['holding_days'],
            'message': 'No congressional trades are stored yet. Sync disclosures before this backtest can produce results.',
        }
    if not trades:
        return {
            'metrics': _empty_metrics(attempted=0),
            'trade_details': [],
            'skipped_details': [],
            'rules': rules,
            'holding_days': rules['holding_days'],
            'message': 'Stored disclosures exist, but none matched the selected chamber, ticker, amount, or action rules.',
        }

    market_cache = {}
    returns = []
    details = []
    skipped = []
    for trade in trades:
        result = calculate_trade_return(trade, rules=rules, market_cache=market_cache)
        if result.get('skipped'):
            skipped.append(result)
            continue
        returns.append(result['return'])
        details.append(result)

    metrics = _metrics(returns, attempted=len(trades), skipped=len(skipped))
    if not returns:
        return {
            'metrics': metrics,
            'trade_details': [],
            'skipped_details': skipped[:50],
            'rules': rules,
            'holding_days': rules['holding_days'],
            'message': 'Disclosures matched the rules, but none had enough market data to complete the replay window.',
        }

    return {
        'metrics': metrics,
        'trade_details': details,
        'skipped_details': skipped[:50],
        'rules': rules,
        'holding_days': rules['holding_days'],
        'message': (
            f"Replayed {len(details)} congressional disclosures with {rules['source']} daily closes, "
            f"entry={rules['entry_basis']}, purchases={rules['purchase_action']}, sales={rules['sale_action']}."
        ),
    }


def calculate_trade_return(trade, rules, market_cache=None):
    market_cache = market_cache if market_cache is not None else {}
    action = _trade_action(trade.get('transaction_type'), rules)
    if action == 'ignore':
        return _skip(trade, 'transaction type ignored by selected rules')

    ticker = _clean_ticker(trade.get('ticker'))
    if not ticker:
        return _skip(trade, 'missing ticker')

    entry_date = _parse_date(trade.get(rules['entry_basis']))
    if not entry_date:
        return _skip(trade, f"missing or invalid {rules['entry_basis']}")

    today = dt.datetime.utcnow().date()
    if entry_date > today:
        return _skip(trade, 'entry date is in the future')

    exit_target = entry_date + dt.timedelta(days=rules['holding_days'])
    if exit_target > today:
        return _skip(trade, 'exit date is in the future')

    market_end = exit_target + dt.timedelta(days=14)
    cache_key = (ticker, entry_date.isoformat(), market_end.isoformat(), rules['source'])
    try:
        data = market_cache.get(cache_key)
        if data is None:
            data = fetch_market_data(ticker, entry_date, market_end, source=rules['source'])
            market_cache[cache_key] = data
    except Exception as exc:
        return _skip(trade, f'market data unavailable: {str(exc)[:180]}')

    entry_bar = _first_price_on_or_after(data, entry_date)
    exit_bar = _first_price_on_or_after(data, exit_target)
    if not entry_bar:
        return _skip(trade, 'no market close at or after entry date')
    if not exit_bar:
        return _skip(trade, 'no market close at or after exit date')

    entry_price = entry_bar['close']
    exit_price = exit_bar['close']
    if entry_price <= 0:
        return _skip(trade, 'entry price is not positive')

    trade_return = (exit_price - entry_price) / entry_price
    if action == 'short':
        trade_return = -trade_return

    return {
        'ticker': ticker,
        'member': trade.get('member'),
        'chamber': trade.get('chamber'),
        'filing_date': trade.get('filing_date'),
        'transaction_date': trade.get('transaction_date'),
        'transaction_type': trade.get('transaction_type'),
        'amount': trade.get('amount'),
        'entry_basis': rules['entry_basis'],
        'entry_date': entry_bar['date'],
        'exit_date': exit_bar['date'],
        'entry_price': entry_price,
        'exit_price': exit_price,
        'action': action,
        'return': trade_return,
        'source': rules['source'],
    }


def fetch_market_data(symbol, start_date, end_date, source='yahoo'):
    if source != 'yahoo':
        raise ValueError(f'Unsupported congressional replay source: {source}')
    client = YahooClient()
    return client.get_chart(
        symbol=symbol,
        timeframe='1d',
        start=start_date.isoformat(),
        end=end_date.isoformat(),
    )


def _normalize_rules(
    holding_days=5,
    entry_basis='filing_date',
    purchase_action='long',
    sale_action='short',
    max_trades=250,
    min_amount=None,
    chambers=None,
    tickers=None,
    source='yahoo',
):
    holding_days = max(1, min(int(holding_days or 5), 365))
    max_trades = max(1, min(int(max_trades or 250), 5000))
    entry_basis = (entry_basis or 'filing_date').strip().lower()
    if entry_basis not in VALID_ENTRY_BASIS:
        raise ValueError(f'entry_basis must be one of: {", ".join(sorted(VALID_ENTRY_BASIS))}')
    source = (source or 'yahoo').strip().lower()
    if source != 'yahoo':
        raise ValueError('Congressional replay currently supports yahoo market data only.')
    chamber_set = _normalize_string_set(chambers)
    ticker_set = _normalize_string_set(tickers)
    return {
        'holding_days': holding_days,
        'entry_basis': entry_basis,
        'purchase_action': _normalize_action(purchase_action, default='long'),
        'sale_action': _normalize_action(sale_action, default='short'),
        'max_trades': max_trades,
        'min_amount': _parse_amount_number(min_amount),
        'chambers': sorted(chamber_set),
        'tickers': sorted(ticker_set),
        'source': source,
    }


def _filter_trades(trades, rules):
    filtered = []
    for trade in trades:
        if rules['chambers'] and (trade.get('chamber') or '').upper() not in rules['chambers']:
            continue
        ticker = _clean_ticker(trade.get('ticker'))
        if rules['tickers'] and ticker not in rules['tickers']:
            continue
        if rules['min_amount'] is not None:
            amount_floor = _parse_amount_number(trade.get('amount'))
            if amount_floor is None or amount_floor < rules['min_amount']:
                continue
        if _trade_action(trade.get('transaction_type'), rules) == 'ignore':
            continue
        filtered.append(trade)
    return filtered


def _normalize_action(value, default):
    action = (value or default).strip().lower()
    if action not in VALID_ACTIONS:
        raise ValueError(f'action must be one of: {", ".join(sorted(VALID_ACTIONS))}')
    return action


def _trade_action(transaction_type, rules):
    normalized = (transaction_type or '').strip().lower()
    if 'sale' in normalized or normalized.startswith('s'):
        return rules['sale_action']
    if 'purchase' in normalized or normalized.startswith('p'):
        return rules['purchase_action']
    return 'ignore'


def _first_price_on_or_after(data, target_date):
    if data is None or getattr(data, 'empty', False):
        return None
    for timestamp, row in data.sort_index().iterrows():
        bar_date = timestamp.date() if hasattr(timestamp, 'date') else _parse_date(str(timestamp))
        if not bar_date or bar_date < target_date:
            continue
        close = row.get('close') if hasattr(row, 'get') else None
        if close is None or not math.isfinite(float(close)):
            continue
        return {'date': bar_date.isoformat(), 'close': float(close)}
    return None


def _metrics(returns, attempted=0, skipped=0):
    if not returns:
        return _empty_metrics(attempted=attempted, skipped=skipped)
    average_return = statistics.mean(returns)
    return_std = statistics.stdev(returns) if len(returns) > 1 else 0
    return {
        'total_trades': len(returns),
        'attempted_trades': attempted,
        'skipped_trades': skipped,
        'total_return': sum(returns),
        'compounded_return': math.prod(1 + value for value in returns) - 1,
        'average_return': average_return,
        'median_return': statistics.median(returns),
        'return_std': return_std,
        'sharpe_ratio': average_return / return_std if return_std else 0,
        'win_rate': sum(1 for value in returns if value > 0) / len(returns),
        'best_return': max(returns),
        'worst_return': min(returns),
    }


def _empty_metrics(attempted=0, skipped=0):
    return {
        'total_trades': 0,
        'attempted_trades': attempted,
        'skipped_trades': skipped,
        'total_return': 0,
        'compounded_return': 0,
        'average_return': 0,
        'median_return': 0,
        'return_std': 0,
        'sharpe_ratio': 0,
        'win_rate': 0,
        'best_return': 0,
        'worst_return': 0,
    }


def _skip(trade, reason):
    return {
        'skipped': True,
        'reason': reason,
        'ticker': trade.get('ticker'),
        'member': trade.get('member'),
        'chamber': trade.get('chamber'),
        'filing_date': trade.get('filing_date'),
        'transaction_date': trade.get('transaction_date'),
        'transaction_type': trade.get('transaction_type'),
    }


def _parse_date(value):
    if not value:
        return None
    try:
        return dt.datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    except ValueError:
        return None


def _parse_amount_number(value):
    if value in (None, ''):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r'[\d,]+(?:\.\d+)?', str(value))
    if not match:
        return None
    return float(match.group(0).replace(',', ''))


def _normalize_string_set(value):
    if not value:
        return set()
    if isinstance(value, str):
        parts = re.split(r'[\s,]+', value)
    else:
        parts = value
    return {str(part).strip().upper() for part in parts if str(part).strip()}


def _clean_ticker(value):
    return (value or '').strip().replace('/', '.').upper()


def _row_to_dict(row):
    return {key: row[key] for key in row.keys()}
