import sqlite3
from datetime import datetime, timezone

import pandas as pd

from utils.etrade_collection import DB_PATH, DATA_DIR


def save_cached_candles(source, symbol, timeframe, candles):
    _ensure_candle_cache()
    clean_source = (source or '').strip().lower()
    clean_symbol = (symbol or '').strip().upper()
    clean_timeframe = (timeframe or '').strip()
    if not clean_source or clean_source == 'cache':
        raise ValueError('Cache writes need the original source name.')
    if not clean_symbol:
        raise ValueError('Cache writes need a symbol.')
    if candles is None or candles.empty:
        return {'inserted_or_updated': 0, 'rows': cache_row_count()}

    collected_at = _now_iso()
    rows = []
    for timestamp, row in candles.iterrows():
        rows.append((
            clean_source,
            clean_symbol,
            clean_timeframe,
            pd.Timestamp(timestamp).isoformat(),
            _float_or_none(row.get('open')),
            _float_or_none(row.get('high')),
            _float_or_none(row.get('low')),
            _float_or_none(row.get('close')),
            _float_or_none(row.get('volume')),
            collected_at,
        ))

    with sqlite3.connect(DB_PATH) as connection:
        connection.executemany(
            """
            insert into market_candles
              (source, symbol, timeframe, timestamp, open, high, low, close, volume, collected_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(source, symbol, timeframe, timestamp)
            do update set
              open = excluded.open,
              high = excluded.high,
              low = excluded.low,
              close = excluded.close,
              volume = excluded.volume,
              collected_at = excluded.collected_at
            """,
            rows,
        )

    return {
        'inserted_or_updated': len(rows),
        'rows': cache_row_count(),
        'source': clean_source,
        'symbol': clean_symbol,
        'timeframe': clean_timeframe,
        'collected_at': collected_at,
    }


def load_cached_candles(symbol, timeframe, start=None, end=None, source=None):
    _ensure_candle_cache()
    clean_symbol = (symbol or '').strip().upper()
    clean_timeframe = (timeframe or '').strip()
    if not clean_symbol:
        raise ValueError('Cached candle symbol is required.')
    if not clean_timeframe:
        raise ValueError('Cached candle timeframe is required.')

    clauses = ['symbol = ?', 'timeframe = ?']
    params = [clean_symbol, clean_timeframe]
    if source:
        clauses.append('source = ?')
        params.append(str(source).strip().lower())
    if start:
        clauses.append('date(timestamp) >= date(?)')
        params.append(start)
    if end:
        clauses.append('date(timestamp) <= date(?)')
        params.append(end)

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"""
            select source, symbol, timeframe, timestamp, open, high, low, close, volume, collected_at
            from market_candles
            where {' and '.join(clauses)}
            order by timestamp asc, collected_at asc
            """,
            params,
        ).fetchall()

    if not rows:
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

    frame = pd.DataFrame([dict(row) for row in rows])
    frame['timestamp'] = pd.to_datetime(frame['timestamp'])
    frame = frame.drop_duplicates(subset=['timestamp'], keep='last')
    frame = frame.set_index('timestamp').sort_index()
    return frame[['open', 'high', 'low', 'close', 'volume']]


def cache_row_count():
    _ensure_candle_cache()
    with sqlite3.connect(DB_PATH) as connection:
        return connection.execute('select count(*) from market_candles').fetchone()[0]


def candle_cache_summary(limit=20):
    _ensure_candle_cache()
    limit = max(1, min(int(limit or 20), 100))
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            select source, symbol, timeframe, count(*) as rows,
                   min(timestamp) as first_timestamp,
                   max(timestamp) as last_timestamp,
                   max(collected_at) as last_collected_at
            from market_candles
            group by source, symbol, timeframe
            order by last_collected_at desc, rows desc
            limit ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def _ensure_candle_cache():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            create table if not exists market_candles (
                id integer primary key autoincrement,
                source text not null,
                symbol text not null,
                timeframe text not null,
                timestamp text not null,
                open real,
                high real,
                low real,
                close real,
                volume real,
                collected_at text not null,
                unique(source, symbol, timeframe, timestamp)
            )
            """
        )
        connection.execute(
            """
            create index if not exists idx_market_candles_lookup
            on market_candles(symbol, timeframe, timestamp)
            """
        )


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _float_or_none(value):
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed
