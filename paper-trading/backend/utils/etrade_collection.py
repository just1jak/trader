import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[2] / 'data'
DB_PATH = DATA_DIR / 'market_data.sqlite'
PENDING_OAUTH_PATH = DATA_DIR / 'etrade_oauth_pending.json'


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


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')
