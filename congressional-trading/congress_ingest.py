import argparse
import html
import io
import re
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

import requests


PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / 'congress_trades.db'
SCHEMA_PATH = PROJECT_ROOT / 'db_schema.sql'

HOUSE_BULK_ZIP_URL = 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.ZIP'
HOUSE_PTR_PDF_URL = 'https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc_id}.pdf'
SENATE_HOME_URL = 'https://efdsearch.senate.gov/search/home/'
SENATE_STOCK_WATCHER_DAILY_URL = (
    'https://raw.githubusercontent.com/timothycarambat/'
    'senate-stock-watcher-data/master/aggregate/all_daily_summaries.json'
)
DATADAWN_STOCK_TRADES_URL = 'https://regs.datadawn.org/openregs/stock_trades.json'
TRADE_UNIQUE_SQL = 'UNIQUE(filing_date, transaction_date, member, ticker, transaction_type, amount, comment, asset_description)'
DEFAULT_HISTORY_START_YEAR = 2012
MAX_DISCLOSURE_LIMIT = 10000
SENATE_PAGE_SIZE = 500

TICKER_WITH_TYPE_RE = re.compile(
    r'(?P<before>.*?)'
    r'(?:\((?P<ticker1>[A-Z][A-Z0-9./-]{0,11})\)|(?P<ticker2>[A-Z][A-Z0-9./-]{0,11}))'
    r'\s+\[(?P<asset_type>[A-Z]{1,4})\](?P<after>.*)$'
)
TRANSACTION_RE = re.compile(
    r'(?P<tx>P(?:urchase)?|S(?:ale)?|E(?:xchange)?)'
    r'(?:\s*\([^)]*\))?\s+'
    r'(?P<date>\d{1,2}/\d{1,2}/\d{4})'
    r'(?P<notification>\d{1,2}/\d{1,2}/\d{4})?'
    r'\s*(?P<amount>\$[\d,]+(?:\s*-\s*\$?[\d,]+)?)'
)


class CongressIngestError(RuntimeError):
    pass


def sync_congressional_disclosures(
    year=None,
    start_year=None,
    end_year=None,
    limit=25,
    include_senate=False,
    all_history=False,
    db_path=DB_PATH,
):
    start_year, end_year = _year_window(year=year, start_year=start_year, end_year=end_year, all_history=all_history)
    limit = _normalize_limit(limit, all_history=all_history)

    house_summaries = []
    house_years = [end_year] if start_year == end_year else []
    house_use_structured = True
    if start_year != end_year:
        try:
            house_summaries.append(
                import_house_datadawn_trades(
                    limit=limit,
                    start_year=start_year,
                    end_year=end_year,
                    db_path=db_path,
                )
            )
        except Exception as exc:
            house_years = list(range(end_year, start_year - 1, -1))
            house_use_structured = False

    for disclosure_year in house_years:
        try:
            house_summaries.append(
                import_house_trades(
                    year=disclosure_year,
                    limit=limit,
                    db_path=db_path,
                    use_structured=house_use_structured,
                )
            )
        except Exception as exc:
            house_summaries.append({
                'source': 'house',
                'status': 'unavailable',
                'year': disclosure_year,
                'reports_available': 0,
                'reports_downloaded': 0,
                'parsed': 0,
                'inserted': 0,
                'errors': [{'year': disclosure_year, 'error': str(exc)[:220]}],
            })
    house = _aggregate_house_summaries(house_summaries)

    senate = {
        'source': 'senate',
        'status': 'skipped',
        'inserted': 0,
        'parsed': 0,
        'errors': [],
    }
    if include_senate:
        senate = import_senate_trades(limit=limit, start_year=start_year, end_year=end_year, db_path=db_path)

    return {
        'status': 'ok' if house.get('status') in {'ok', 'empty'} and senate.get('status') != 'unavailable' else 'partial',
        'year': end_year,
        'start_year': start_year,
        'end_year': end_year,
        'all_history': bool(all_history),
        'limit': limit,
        'request': {
            'year': year,
            'start_year': start_year,
            'end_year': end_year,
            'all_history': bool(all_history),
            'limit': limit,
            'include_senate': bool(include_senate),
        },
        'house': house,
        'senate': senate,
        'counts': disclosure_counts(db_path=db_path),
    }


def import_house_trades(year=None, limit=25, db_path=DB_PATH, use_structured=True):
    year = int(year or datetime.utcnow().year)
    limit = _normalize_limit(limit, all_history=limit is None)
    ensure_schema(db_path)
    errors = []

    if use_structured:
        try:
            structured = import_house_datadawn_trades(limit=limit, start_year=year, end_year=year, db_path=db_path)
            if structured.get('parsed'):
                return structured
        except Exception as exc:
            errors.append({'source': 'datadawn_openregs', 'year': year, 'error': str(exc)[:220]})

    response = requests.get(HOUSE_BULK_ZIP_URL.format(year=year), timeout=30)
    if response.status_code >= 400:
        raise CongressIngestError(f'House disclosure index fetch failed with HTTP {response.status_code}.')

    reports = _house_ptr_reports(response.content)
    selected = reports if limit is None else reports[:limit]
    inserted = 0
    parsed = 0

    with sqlite3.connect(db_path) as connection:
        for report in selected:
            try:
                pdf = requests.get(
                    HOUSE_PTR_PDF_URL.format(year=report['year'], doc_id=report['doc_id']),
                    timeout=30,
                )
                if pdf.status_code >= 400:
                    raise CongressIngestError(f"PTR PDF {report['doc_id']} returned HTTP {pdf.status_code}.")

                trades = parse_house_ptr_pdf(pdf.content)
                parsed += len(trades)
                for trade in trades:
                    inserted += _insert_house_trade(connection, report, trade)
            except Exception as exc:
                errors.append({
                    'source': 'house_ptr_pdf',
                    'doc_id': report.get('doc_id'),
                    'member': report.get('member'),
                    'error': str(exc)[:220],
                })

    return {
        'source': 'house',
        'status': 'ok' if parsed else 'empty',
        'year': year,
        'reports_available': len(reports),
        'reports_downloaded': len(selected),
        'parsed': parsed,
        'inserted': inserted,
        'errors': errors[:10],
    }


def import_house_datadawn_trades(limit=25, start_year=None, end_year=None, db_path=DB_PATH):
    ensure_schema(db_path)
    limit = _normalize_limit(limit, all_history=limit is None)
    start_year, end_year = _year_window(start_year=start_year, end_year=end_year)
    rows, available = _fetch_datadawn_stock_trades('House', limit, start_year=start_year, end_year=end_year)
    inserted = 0
    with sqlite3.connect(db_path) as connection:
        for row in rows:
            inserted += _insert_house_datadawn_trade(connection, row)
    return {
        'source': 'datadawn_openregs_house',
        'status': 'ok' if rows else 'empty',
        'year': end_year,
        'start_year': start_year,
        'end_year': end_year,
        'reports_available': available,
        'reports_downloaded': len(rows),
        'parsed': len(rows),
        'inserted': inserted,
        'errors': [],
    }


def import_senate_trades(limit=25, start_year=None, end_year=None, db_path=DB_PATH):
    ensure_schema(db_path)
    limit = _normalize_limit(limit, all_history=limit is None)
    start_year, end_year = _year_window(start_year=start_year, end_year=end_year)
    errors = []

    try:
        response = requests.get(SENATE_HOME_URL, timeout=20)
        if response.status_code >= 400:
            errors.append(f'Official Senate eFD returned HTTP {response.status_code}; using structured fallback.')
    except Exception as exc:
        errors.append(f'Official Senate eFD unavailable: {str(exc)[:180]}; using structured fallback.')

    try:
        rows, available = _fetch_datadawn_stock_trades('Senate', limit, start_year=start_year, end_year=end_year)
        inserted = 0
        with sqlite3.connect(db_path) as connection:
            for row in rows:
                inserted += _insert_senate_datadawn_trade(connection, row)
        return {
            'source': 'datadawn_openregs',
            'status': 'ok' if rows else 'empty',
            'reports_available': available,
            'reports_downloaded': len(rows),
            'inserted': inserted,
            'parsed': len(rows),
            'start_year': start_year,
            'end_year': end_year,
            'errors': errors[:10],
        }
    except Exception as exc:
        errors.append(f'DataDawn Senate fallback unavailable: {str(exc)[:180]}; using historical GitHub fallback.')

    try:
        response = requests.get(SENATE_STOCK_WATCHER_DAILY_URL, timeout=30)
        if response.status_code >= 400:
            raise CongressIngestError(f'Senate fallback dataset returned HTTP {response.status_code}.')
        summaries = response.json()
    except Exception as exc:
        return {
            'source': 'senate',
            'status': 'unavailable',
            'inserted': 0,
            'parsed': 0,
            'errors': errors + [str(exc)[:220]],
        }

    reports = sorted(
        (
            summary for summary in summaries
            if summary.get('transactions') and _report_in_year_window(summary, start_year=start_year, end_year=end_year)
        ),
        key=lambda item: (_normalize_date(item.get('date_recieved') or item.get('date_received')), item.get('ptr_link') or ''),
        reverse=True,
    )
    selected = reports if limit is None else reports[:limit]
    inserted = 0
    parsed = 0

    with sqlite3.connect(db_path) as connection:
        for report in selected:
            transactions = report.get('transactions') or []
            parsed += len(transactions)
            for trade in transactions:
                inserted += _insert_senate_trade(connection, report, trade)

    return {
        'source': 'senate_stock_watcher',
        'status': 'ok' if parsed else 'empty',
        'reports_available': len(reports),
        'reports_downloaded': len(selected),
        'inserted': inserted,
        'parsed': parsed,
        'start_year': start_year,
        'end_year': end_year,
        'errors': errors[:10],
    }


def parse_house_ptr_pdf(pdf_bytes):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise CongressIngestError('pypdf is required to parse House PTR PDFs. Run pip install -r requirements.txt.') from exc

    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = '\n'.join(page.extract_text() or '' for page in reader.pages)
    return parse_house_ptr_text(text)


def parse_house_ptr_text(text):
    cleaned = (
        text.replace('\x00', '')
        .replace(chr(8211), '-')
        .replace(chr(8212), '-')
        .replace('\xa0', ' ')
    )
    lines = [re.sub(r'\s+', ' ', line).strip() for line in cleaned.splitlines()]
    lines = [line for line in lines if line]

    trades = []
    seen = set()
    for index, line in enumerate(lines):
        bracket_index = index
        candidate = line

        if re.fullmatch(r'\[[A-Z]{1,4}\]', line) and index > 0:
            candidate = f'{lines[index - 1]} {line}'
        elif index + 1 < len(lines) and re.fullmatch(r'\[[A-Z]{1,4}\]', lines[index + 1]):
            candidate = f'{line} {lines[index + 1]}'
            bracket_index = index + 1

        match = TICKER_WITH_TYPE_RE.search(candidate)
        if not match:
            continue
        if (match.group('asset_type') or '').upper() != 'ST':
            continue

        detail = (match.group('after') or '').strip()
        cursor = bracket_index + 1
        while not TRANSACTION_RE.search(detail) and cursor < len(lines) and cursor <= bracket_index + 3:
            detail = f'{detail} {lines[cursor]}'.strip()
            cursor += 1

        transaction = TRANSACTION_RE.search(detail)
        if not transaction:
            continue

        amount = transaction.group('amount')
        if '-' not in amount and detail.rstrip().endswith('-') and cursor < len(lines):
            continuation = re.match(r'^\$?[\d,]+', lines[cursor])
            if continuation:
                amount = f'{amount} - {continuation.group(0)}'

        ticker = _normalize_ticker(match.group('ticker1') or match.group('ticker2'))
        if not _looks_like_ticker(ticker):
            continue

        asset = _asset_description(lines, index, candidate, match)
        trade = {
            'ticker': ticker,
            'asset_description': asset,
            'transaction_type': _transaction_type(transaction.group('tx')),
            'transaction_date': _normalize_date(transaction.group('date')),
            'amount': _clean_amount(amount),
            'comment': '',
        }
        key = (trade['ticker'], trade['transaction_type'], trade['transaction_date'], trade['amount'])
        if key in seen:
            continue
        seen.add(key)
        trades.append(trade)

    return trades


def disclosure_counts(db_path=DB_PATH):
    ensure_schema(db_path)
    with sqlite3.connect(db_path) as connection:
        house = connection.execute('select count(*) from house_trades').fetchone()[0]
        senate = connection.execute('select count(*) from senate_trades').fetchone()[0]
    return {'house': house, 'senate': senate, 'total': house + senate}


def _year_window(year=None, start_year=None, end_year=None, all_history=False):
    current_year = datetime.utcnow().year
    if all_history:
        start = int(start_year or DEFAULT_HISTORY_START_YEAR)
        end = int(end_year or current_year)
    elif start_year is not None or end_year is not None:
        start = int(start_year or end_year or year or current_year)
        end = int(end_year or start_year or year or current_year)
    else:
        start = end = int(year or current_year)

    if start > end:
        start, end = end, start
    end = min(end, current_year)
    return start, end


def _normalize_limit(limit, all_history=False):
    if limit in (None, '', 'all'):
        return None if all_history or limit == 'all' else 25
    value = int(limit)
    if value <= 0:
        return None
    return min(value, MAX_DISCLOSURE_LIMIT)


def _aggregate_house_summaries(summaries):
    errors = []
    for summary in summaries:
        errors.extend(summary.get('errors') or [])
    parsed = sum(summary.get('parsed') or 0 for summary in summaries)
    unavailable = any(summary.get('status') == 'unavailable' for summary in summaries)
    status = 'partial' if unavailable else 'ok'
    if not parsed and not unavailable:
        status = 'empty'

    return {
        'source': 'house',
        'status': status,
        'years': summaries,
        'reports_available': sum(summary.get('reports_available') or 0 for summary in summaries),
        'reports_downloaded': sum(summary.get('reports_downloaded') or 0 for summary in summaries),
        'parsed': parsed,
        'inserted': sum(summary.get('inserted') or 0 for summary in summaries),
        'errors': errors[:20],
    }


def ensure_schema(db_path=DB_PATH):
    db_path = Path(db_path)
    schema = SCHEMA_PATH.read_text()
    with sqlite3.connect(db_path) as connection:
        connection.executescript(schema)
        _migrate_trade_unique(connection, 'house_trades', 'district')
        _migrate_trade_unique(connection, 'senate_trades', 'state')


def _migrate_trade_unique(connection, table, region_column):
    current = connection.execute(
        "select sql from sqlite_master where type = 'table' and name = ?",
        (table,),
    ).fetchone()
    if not current or TRADE_UNIQUE_SQL in (current[0] or ''):
        return

    backup = f'{table}_old_unique'
    connection.execute(f'drop table if exists {backup}')
    connection.execute(f'alter table {table} rename to {backup}')
    connection.execute(
        f"""
        create table {table} (
            id integer primary key autoincrement,
            filing_date text,
            transaction_date text,
            member text,
            {region_column} text,
            ticker text,
            asset_description text,
            transaction_type text,
            amount text,
            comment text,
            {TRADE_UNIQUE_SQL}
        )
        """
    )
    connection.execute(
        f"""
        insert or ignore into {table}
          (id, filing_date, transaction_date, member, {region_column}, ticker,
           asset_description, transaction_type, amount, comment)
        select id, filing_date, transaction_date, member, {region_column}, ticker,
               asset_description, transaction_type, amount, comment
        from {backup}
        """
    )
    connection.execute(f'drop table {backup}')


def _house_ptr_reports(zip_bytes):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        xml_name = next((name for name in archive.namelist() if name.lower().endswith('.xml')), None)
        if not xml_name:
            raise CongressIngestError('House disclosure ZIP did not contain an XML index.')
        root = ET.fromstring(archive.read(xml_name).decode('utf-8-sig'))

    reports = []
    for member in root.findall('Member'):
        if (member.findtext('FilingType') or '').strip().upper() != 'P':
            continue
        filing_date = _normalize_date(member.findtext('FilingDate'))
        first = (member.findtext('First') or '').strip()
        last = (member.findtext('Last') or '').strip()
        prefix = (member.findtext('Prefix') or '').strip()
        reports.append({
            'doc_id': (member.findtext('DocID') or '').strip(),
            'year': int(member.findtext('Year') or datetime.utcnow().year),
            'filing_date': filing_date,
            'member': ' '.join(part for part in [prefix, first, last] if part),
            'district': (member.findtext('StateDst') or '').strip(),
        })

    reports.sort(key=lambda item: (item['filing_date'], item['doc_id']), reverse=True)
    return reports


def _insert_house_trade(connection, report, trade):
    cursor = connection.execute(
        """
        insert into house_trades
          (filing_date, transaction_date, member, district, ticker,
           asset_description, transaction_type, amount, comment)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(filing_date, transaction_date, member, ticker, transaction_type, amount, comment, asset_description)
        do update set
          district = excluded.district,
          asset_description = excluded.asset_description,
          amount = excluded.amount,
          comment = excluded.comment
        """,
        (
            report['filing_date'],
            trade['transaction_date'],
            report['member'],
            report['district'],
            trade['ticker'],
            trade['asset_description'],
            trade['transaction_type'],
            trade['amount'],
            f"source=house_ptr; doc_id={report['doc_id']}",
        ),
    )
    return 1 if cursor.rowcount == 1 else 0


def _insert_senate_trade(connection, report, trade):
    filing_date = _normalize_date(report.get('date_recieved') or report.get('date_received'))
    member = _senate_member_name(report)
    ticker = _normalize_ticker(_clean_html(trade.get('ticker') or ''))
    if not _looks_like_ticker(ticker):
        return 0
    transaction_type = _transaction_type(trade.get('type'))
    asset_description = _clean_html(trade.get('asset_description') or ticker)
    comment_parts = [
        'source=senate_stock_watcher',
        f"ptr_link={report.get('ptr_link') or ''}",
    ]
    if trade.get('owner'):
        comment_parts.append(f"owner={trade.get('owner')}")
    if trade.get('asset_type'):
        comment_parts.append(f"asset_type={trade.get('asset_type')}")
    if report.get('bioguide'):
        comment_parts.append(f"bioguide={report.get('bioguide')}")
    if trade.get('comment') and trade.get('comment') != '--':
        comment_parts.append(f"comment={_clean_html(trade.get('comment'))}")

    cursor = connection.execute(
        """
        insert into senate_trades
          (filing_date, transaction_date, member, state, ticker,
           asset_description, transaction_type, amount, comment)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(filing_date, transaction_date, member, ticker, transaction_type, amount, comment, asset_description)
        do update set
          state = excluded.state,
          asset_description = excluded.asset_description,
          amount = excluded.amount,
          comment = excluded.comment
        """,
        (
            filing_date,
            _normalize_date(trade.get('transaction_date')),
            member,
            '',
            ticker,
            asset_description[:240],
            transaction_type,
            _clean_amount(trade.get('amount')),
            '; '.join(part for part in comment_parts if part)[:500],
        ),
    )
    return 1 if cursor.rowcount == 1 else 0


def _fetch_datadawn_senate_trades(limit, start_year=None, end_year=None):
    return _fetch_datadawn_stock_trades('Senate', limit, start_year=start_year, end_year=end_year)


def _fetch_datadawn_stock_trades(chamber, limit, start_year=None, end_year=None):
    has_year_filter = start_year is not None or end_year is not None
    page_size = SENATE_PAGE_SIZE if has_year_filter else min(limit or SENATE_PAGE_SIZE, SENATE_PAGE_SIZE)
    page_size = max(1, page_size)
    max_pages = 200 if limit is None or has_year_filter else max(1, (limit // page_size) + 8)
    next_cursor = None
    rows = []
    available = 0
    seen = set()

    for _ in range(max_pages):
        params = {
            '_size': page_size,
            '_sort_desc': 'transaction_date',
            'chamber': chamber,
            'ticker__notblank': '1',
        }
        if next_cursor:
            params['_next'] = next_cursor

        response = requests.get(
            DATADAWN_STOCK_TRADES_URL,
            params=params,
            timeout=30,
        )
        if response.status_code >= 400:
            raise CongressIngestError(f'DataDawn stock_trades returned HTTP {response.status_code}.')
        payload = response.json()
        page_rows = _datadawn_rows_from_payload(payload)
        available = max(available, int(payload.get('filtered_table_rows_count') or len(page_rows)))
        if not page_rows:
            break

        new_rows = 0
        page_years = []
        for row in page_rows:
            key = row.get('id') or tuple(sorted((str(k), str(v)) for k, v in row.items()))
            if key in seen:
                continue
            seen.add(key)
            new_rows += 1
            row_year = _row_year(row)
            if row_year:
                page_years.append(row_year)
            if _row_in_year_window(row, start_year=start_year, end_year=end_year):
                rows.append(row)
                if limit is not None and len(rows) >= limit:
                    return rows[:limit], available

        if new_rows == 0 or len(page_rows) < page_size:
            break
        if start_year and page_years and max(page_years) < start_year:
            break
        next_cursor = payload.get('next')
        if not next_cursor:
            break

    return rows, available


def _datadawn_rows_from_payload(payload):
    raw_rows = payload.get('rows') or []
    if not raw_rows:
        return []
    if isinstance(raw_rows[0], dict):
        return raw_rows
    columns = payload.get('columns') or []
    return [dict(zip(columns, row)) for row in raw_rows]


def _insert_house_datadawn_trade(connection, row):
    ticker = _normalize_ticker(row.get('ticker'))
    if not _looks_like_ticker(ticker):
        return 0

    comment_parts = [
        'source=datadawn_openregs',
        f"source_url={row.get('source_url') or ''}",
        f"datadawn_id={row.get('id') or ''}",
    ]
    if row.get('doc_id'):
        comment_parts.append(f"doc_id={row.get('doc_id')}")
    if row.get('owner'):
        comment_parts.append(f"owner={row.get('owner')}")
    if row.get('asset_type'):
        comment_parts.append(f"asset_type={row.get('asset_type')}")
    if row.get('bioguide_id'):
        comment_parts.append(f"bioguide={row.get('bioguide_id')}")
    if row.get('cik'):
        comment_parts.append(f"cik={row.get('cik')}")
    if row.get('comment'):
        comment_parts.append(f"comment={_clean_html(row.get('comment'))}")

    cursor = connection.execute(
        """
        insert into house_trades
          (filing_date, transaction_date, member, district, ticker,
           asset_description, transaction_type, amount, comment)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(filing_date, transaction_date, member, ticker, transaction_type, amount, comment, asset_description)
        do update set
          district = excluded.district,
          asset_description = excluded.asset_description,
          amount = excluded.amount,
          comment = excluded.comment
        """,
        (
            _normalize_date(row.get('disclosure_date')),
            _normalize_date(row.get('transaction_date')),
            row.get('member_name') or '',
            row.get('state_district') or '',
            ticker,
            _clean_html(row.get('asset_description') or ticker)[:240],
            _transaction_type(row.get('transaction_type')),
            _clean_amount(row.get('amount_range')),
            '; '.join(part for part in comment_parts if part)[:500],
        ),
    )
    return 1 if cursor.rowcount == 1 else 0


def _insert_senate_datadawn_trade(connection, row):
    ticker = _normalize_ticker(row.get('ticker'))
    if not _looks_like_ticker(ticker):
        return 0

    comment_parts = [
        'source=datadawn_openregs',
        f"source_url={row.get('source_url') or ''}",
        f"datadawn_id={row.get('id') or ''}",
    ]
    if row.get('owner'):
        comment_parts.append(f"owner={row.get('owner')}")
    if row.get('asset_type'):
        comment_parts.append(f"asset_type={row.get('asset_type')}")
    if row.get('bioguide_id'):
        comment_parts.append(f"bioguide={row.get('bioguide_id')}")
    if row.get('cik'):
        comment_parts.append(f"cik={row.get('cik')}")
    if not row.get('disclosure_date'):
        comment_parts.append('disclosure_date_missing=true')
    if row.get('comment'):
        comment_parts.append(f"comment={_clean_html(row.get('comment'))}")

    cursor = connection.execute(
        """
        insert into senate_trades
          (filing_date, transaction_date, member, state, ticker,
           asset_description, transaction_type, amount, comment)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(filing_date, transaction_date, member, ticker, transaction_type, amount, comment, asset_description)
        do update set
          state = excluded.state,
          asset_description = excluded.asset_description,
          amount = excluded.amount,
          comment = excluded.comment
        """,
        (
            _normalize_date(row.get('disclosure_date')),
            _normalize_date(row.get('transaction_date')),
            row.get('member_name') or '',
            row.get('state_district') or '',
            ticker,
            _clean_html(row.get('asset_description') or ticker)[:240],
            _transaction_type(row.get('transaction_type')),
            _clean_amount(row.get('amount_range')),
            '; '.join(part for part in comment_parts if part)[:500],
        ),
    )
    return 1 if cursor.rowcount == 1 else 0


def _senate_member_name(report):
    first = (report.get('first_name') or '').strip()
    last = (report.get('last_name') or '').strip()
    if first or last:
        return ' '.join(part for part in [first, last] if part)
    office = report.get('office') or ''
    return re.sub(r'\s*\([^)]*\)\s*$', '', office).strip()


def _clean_html(value):
    text = re.sub(r'<[^>]+>', ' ', value or '')
    return re.sub(r'\s+', ' ', html.unescape(text)).strip(' -')


def _asset_description(lines, index, candidate, match):
    before = (match.group('before') or '').strip(' -')
    parts = [before] if before else []

    if not parts or _is_generic_asset_prefix(before):
        for previous in reversed(lines[max(0, index - 3):index]):
            if _line_is_metadata(previous):
                if parts:
                    break
                continue
            if parts and previous[:1].islower():
                break
            if TRANSACTION_RE.search(previous):
                continue
            parts.insert(0, previous)
            if len(' '.join(parts)) >= 90:
                break

    asset = ' '.join(part for part in parts if part).strip(' -')
    ticker = match.group('ticker1') or match.group('ticker2') or ''
    if not asset:
        asset = ticker
    return asset[:240]


def _line_is_metadata(line):
    if line in {'ID Owner Asset Transaction', 'Type', 'Date Notification', 'Date', 'Amount Cap.', 'Gains >', '$200?'}:
        return True
    if line.startswith(('Clerk of ', 'Name:', 'Status:', 'State/District:', 'Filing ID', 'Digitally Signed', '* For ')):
        return True
    if line.startswith(('C:', 'D:')):
        return True
    if ':' in line and line[:2] in {'F ', 'S ', 'D ', 'L ', 'I ', 'C '}:
        return True
    if 'shares sold @' in line:
        return True
    return False


def _is_generic_asset_prefix(value):
    normalized = (value or '').strip().lower()
    return normalized in {'stock', 'common stock', 'new common stock'} or len(normalized) < 8


def _normalize_ticker(value):
    return (value or '').strip().replace('/', '.').upper()


def _looks_like_ticker(value):
    if not value or len(value) > 12:
        return False
    return bool(re.fullmatch(r'[A-Z][A-Z0-9.:-]*', value))


def _transaction_type(value):
    value = (value or '').strip().upper()
    if value.startswith('S'):
        return 'Sale'
    if value.startswith('E'):
        return 'Exchange'
    return 'Purchase'


def _row_in_year_window(row, start_year=None, end_year=None):
    year = _row_year(row)
    if not year:
        return True
    if start_year is not None and year < int(start_year):
        return False
    if end_year is not None and year > int(end_year):
        return False
    return True


def _row_year(row):
    for key in ('disclosure_date', 'transaction_date', 'filing_date', 'date_received', 'date_recieved'):
        normalized = _normalize_date(row.get(key))
        if normalized[:4].isdigit():
            return int(normalized[:4])
    return None


def _report_in_year_window(report, start_year=None, end_year=None):
    year = _row_year({
        'disclosure_date': report.get('date_recieved') or report.get('date_received'),
        'transaction_date': report.get('transaction_date'),
    })
    if year is None:
        return True
    if start_year is not None and year < int(start_year):
        return False
    if end_year is not None and year > int(end_year):
        return False
    return True


def _normalize_date(value):
    value = (value or '').strip()
    if not value:
        return ''
    for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(value, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return value


def _clean_amount(value):
    return re.sub(r'\s+', ' ', value or '').strip()


def main():
    parser = argparse.ArgumentParser(description='Import congressional disclosure trades into SQLite.')
    parser.add_argument('--year', type=int)
    parser.add_argument('--start-year', type=int)
    parser.add_argument('--end-year', type=int)
    parser.add_argument('--limit', type=int, default=25, help='Per-year/source cap; use 0 for uncapped.')
    parser.add_argument('--all-history', action='store_true')
    parser.add_argument('--include-senate', action='store_true')
    parser.add_argument('--db', default=str(DB_PATH))
    args = parser.parse_args()
    summary = sync_congressional_disclosures(
        year=args.year,
        start_year=args.start_year,
        end_year=args.end_year,
        limit=args.limit,
        all_history=args.all_history,
        include_senate=args.include_senate,
        db_path=Path(args.db),
    )
    print(summary)


if __name__ == '__main__':
    main()
