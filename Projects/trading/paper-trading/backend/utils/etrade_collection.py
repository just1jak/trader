import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[2] / 'data'
DB_PATH = DATA_DIR / 'market_data.sqlite'
PENDING_OAUTH_PATH = DATA_DIR / 'etrade_oauth_pending.json'
PAPER_STRATEGIES = {'forward_long', 'forward_short', 'observe_only'}
PRICE_KEYS = (
    'lastTrade',
    'lastPrice',
    'last',
    'price',
    'marketPrice',
    'intradayPrice',
    'bid',
    'ask',
    'close',
)


def save_pending_oauth(payload):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        'oauth_token': payload['oauth_token'],
        'oauth_token_secret': payload['oauth_token_secret'],
        'oauth_callback_confirmed': payload.get('oauth_callback_confirmed'),
        'created_at': _now_iso(),
    }
    PENDING_OAUTH_PATH.write_text(json.dumps(record, indent=2))
    return {
        'oauth_token': record['oauth_token'],
        'oauth_callback_confirmed': record.get('oauth_callback_confirmed'),
        'created_at': record['created_at'],
    }


def load_pending_oauth():
    if not PENDING_OAUTH_PATH.exists():
        return {}
    return json.loads(PENDING_OAUTH_PATH.read_text())


def clear_pending_oauth():
    if PENDING_OAUTH_PATH.exists():
        PENDING_OAUTH_PATH.unlink()


def save_market_snapshot(snapshot_type, symbol, request_params, response_payload):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _ensure_db()
    captured_at = _now_iso()
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            """
            insert into etrade_market_snapshots
              (captured_at, snapshot_type, symbol, request_json, response_json)
            values (?, ?, ?, ?, ?)
            """,
            (
                captured_at,
                snapshot_type,
                symbol,
                json.dumps(request_params, sort_keys=True),
                json.dumps(response_payload, sort_keys=True),
            ),
        )
        snapshot_id = cursor.lastrowid
    return {
        'id': snapshot_id,
        'captured_at': captured_at,
        'snapshot_type': snapshot_type,
        'symbol': symbol,
    }


def list_market_snapshots(limit=25):
    _ensure_db()
    limit = max(1, min(int(limit or 25), 100))
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            select id, captured_at, snapshot_type, symbol, request_json
            from etrade_market_snapshots
            order by id desc
            limit ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            'id': row['id'],
            'captured_at': row['captured_at'],
            'snapshot_type': row['snapshot_type'],
            'symbol': row['symbol'],
            'request': json.loads(row['request_json'] or '{}'),
        }
        for row in rows
    ]


def create_paper_session(name, symbol, strategy='forward_long', quantity=1, initial_cash=100000, notes=''):
    _ensure_db()
    clean_symbol = (symbol or '').strip().upper()
    clean_name = (name or clean_symbol or 'Forward paper session').strip()
    clean_strategy = strategy or 'forward_long'
    numeric_quantity = _positive_float(quantity, 'quantity')
    numeric_cash = _positive_float(initial_cash, 'initial_cash')

    if not clean_symbol:
        raise ValueError('Paper session symbol is required')
    if clean_strategy not in PAPER_STRATEGIES:
        raise ValueError(f'Unsupported paper strategy: {clean_strategy}')

    created_at = _now_iso()
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            """
            insert into paper_forward_sessions
              (created_at, name, symbol, strategy, quantity, initial_cash, status, notes)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                clean_name,
                clean_symbol,
                clean_strategy,
                numeric_quantity,
                numeric_cash,
                'active',
                notes or '',
            ),
        )
        session_id = cursor.lastrowid
    return get_paper_session(session_id)


def get_paper_session(session_id):
    _ensure_db()
    session_id = _required_int(session_id, 'session_id')
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            select id, created_at, name, symbol, strategy, quantity, initial_cash, status, notes
            from paper_forward_sessions
            where id = ?
            """,
            (session_id,),
        ).fetchone()
    if row is None:
        raise ValueError(f'Paper session not found: {session_id}')
    return _paper_session_from_row(row)


def list_paper_sessions(limit=50):
    _ensure_db()
    limit = max(1, min(int(limit or 50), 100))
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            select
                s.id,
                s.created_at,
                s.name,
                s.symbol,
                s.strategy,
                s.quantity,
                s.initial_cash,
                s.status,
                s.notes,
                m.id as latest_mark_id,
                m.captured_at as latest_captured_at,
                m.price as latest_price,
                m.position as latest_position,
                m.cash as latest_cash,
                m.equity as latest_equity,
                m.pnl as latest_pnl,
                m.signal as latest_signal
            from paper_forward_sessions s
            left join paper_forward_marks m
              on m.id = (
                select id
                from paper_forward_marks
                where session_id = s.id
                order by id desc
                limit 1
              )
            order by s.id desc
            limit ?
            """,
            (limit,),
        ).fetchall()
    return [_paper_session_with_latest_from_row(row) for row in rows]


def mark_paper_session(session_id, price, raw_payload=None, source_snapshot_id=None):
    _ensure_db()
    session = get_paper_session(session_id)
    numeric_price = _positive_float(price, 'price')
    captured_at = _now_iso()

    latest_mark = _latest_paper_mark(session['id'])
    if latest_mark:
        position = latest_mark['position']
        cash = latest_mark['cash']
        signal = 'observed' if session['strategy'] == 'observe_only' else 'marked'
    elif session['strategy'] == 'forward_short':
        position = -session['quantity']
        cash = session['initial_cash'] + session['quantity'] * numeric_price
        signal = 'entered_short'
    elif session['strategy'] == 'observe_only':
        position = 0
        cash = session['initial_cash']
        signal = 'observed'
    else:
        position = session['quantity']
        cash = session['initial_cash'] - session['quantity'] * numeric_price
        signal = 'entered_long'

    equity = cash + position * numeric_price
    pnl = equity - session['initial_cash']
    raw_json = json.dumps(raw_payload or {}, sort_keys=True)

    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            """
            insert into paper_forward_marks
              (session_id, captured_at, symbol, price, quantity, position, cash, equity, pnl, signal, source_snapshot_id, raw_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session['id'],
                captured_at,
                session['symbol'],
                numeric_price,
                session['quantity'],
                position,
                cash,
                equity,
                pnl,
                signal,
                source_snapshot_id,
                raw_json,
            ),
        )
        mark_id = cursor.lastrowid
    return _get_paper_mark(mark_id)


def list_paper_marks(session_id, limit=100):
    _ensure_db()
    session_id = _required_int(session_id, 'session_id')
    limit = max(1, min(int(limit or 100), 250))
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            select id, session_id, captured_at, symbol, price, quantity, position, cash,
                   equity, pnl, signal, source_snapshot_id
            from paper_forward_marks
            where session_id = ?
            order by id desc
            limit ?
            """,
            (session_id, limit),
        ).fetchall()
    return [_paper_mark_from_row(row) for row in rows]


def extract_quote_price(payload):
    found = _walk_for_price(payload)
    if found is None:
        raise ValueError('Could not find a usable price in the E*TRADE quote payload')
    price, field = found
    return {'price': price, 'field': field}


def _ensure_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            create table if not exists etrade_market_snapshots (
                id integer primary key autoincrement,
                captured_at text not null,
                snapshot_type text not null,
                symbol text not null,
                request_json text not null,
                response_json text not null
            )
            """
        )
        connection.execute(
            """
            create index if not exists idx_etrade_market_snapshots_type_time
            on etrade_market_snapshots(snapshot_type, captured_at)
            """
        )
        connection.execute(
            """
            create table if not exists paper_forward_sessions (
                id integer primary key autoincrement,
                created_at text not null,
                name text not null,
                symbol text not null,
                strategy text not null,
                quantity real not null,
                initial_cash real not null,
                status text not null,
                notes text not null
            )
            """
        )
        connection.execute(
            """
            create table if not exists paper_forward_marks (
                id integer primary key autoincrement,
                session_id integer not null,
                captured_at text not null,
                symbol text not null,
                price real not null,
                quantity real not null,
                position real not null,
                cash real not null,
                equity real not null,
                pnl real not null,
                signal text not null,
                source_snapshot_id integer,
                raw_json text not null,
                foreign key(session_id) references paper_forward_sessions(id)
            )
            """
        )
        connection.execute(
            """
            create index if not exists idx_paper_forward_marks_session_time
            on paper_forward_marks(session_id, captured_at)
            """
        )


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _paper_session_from_row(row):
    return {
        'id': row['id'],
        'created_at': row['created_at'],
        'name': row['name'],
        'symbol': row['symbol'],
        'strategy': row['strategy'],
        'quantity': row['quantity'],
        'initial_cash': row['initial_cash'],
        'status': row['status'],
        'notes': row['notes'],
    }


def _paper_session_with_latest_from_row(row):
    session = _paper_session_from_row(row)
    session['latest_mark'] = None
    if row['latest_mark_id'] is not None:
        session['latest_mark'] = {
            'id': row['latest_mark_id'],
            'session_id': row['id'],
            'captured_at': row['latest_captured_at'],
            'symbol': row['symbol'],
            'price': row['latest_price'],
            'position': row['latest_position'],
            'cash': row['latest_cash'],
            'equity': row['latest_equity'],
            'pnl': row['latest_pnl'],
            'signal': row['latest_signal'],
            'source_snapshot_id': None,
        }
    return session


def _get_paper_mark(mark_id):
    mark_id = _required_int(mark_id, 'mark_id')
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            select id, session_id, captured_at, symbol, price, quantity, position, cash,
                   equity, pnl, signal, source_snapshot_id
            from paper_forward_marks
            where id = ?
            """,
            (mark_id,),
        ).fetchone()
    return _paper_mark_from_row(row)


def _latest_paper_mark(session_id):
    session_id = _required_int(session_id, 'session_id')
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            select id, session_id, captured_at, symbol, price, quantity, position, cash,
                   equity, pnl, signal, source_snapshot_id
            from paper_forward_marks
            where session_id = ?
            order by id desc
            limit 1
            """,
            (session_id,),
        ).fetchone()
    return _paper_mark_from_row(row) if row else None


def _paper_mark_from_row(row):
    return {
        'id': row['id'],
        'session_id': row['session_id'],
        'captured_at': row['captured_at'],
        'symbol': row['symbol'],
        'price': row['price'],
        'quantity': row['quantity'],
        'position': row['position'],
        'cash': row['cash'],
        'equity': row['equity'],
        'pnl': row['pnl'],
        'signal': row['signal'],
        'source_snapshot_id': row['source_snapshot_id'],
    }


def _positive_float(value, label):
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{label} must be a number') from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise ValueError(f'{label} must be greater than zero')
    return parsed


def _required_int(value, label):
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{label} is required') from exc


def _walk_for_price(value):
    if isinstance(value, dict):
        for key in PRICE_KEYS:
            if key in value:
                parsed = _float_or_none(value[key])
                if parsed is not None:
                    return parsed, key
        for item in value.values():
            found = _walk_for_price(item)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _walk_for_price(item)
            if found is not None:
                return found
    return None


def _float_or_none(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.replace(',', '').replace('$', '').strip()
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed) or parsed <= 0:
        return None
    return parsed
