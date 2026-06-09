import pandas as pd
import requests


class YahooConfigError(RuntimeError):
    pass


class YahooClient:
    BASE_URL = 'https://query1.finance.yahoo.com/v8/finance/chart'

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0',
        })

    def get_chart(self, symbol='AAPL', timeframe='1d', start=None, end=None):
        clean_symbol = (symbol or 'AAPL').strip().upper()
        interval = _timeframe_to_interval(timeframe)
        period1 = _to_unix(start or '2025-01-02')
        period2 = _to_unix(end or start or '2025-01-31', include_full_day=True)
        if period2 <= period1:
            raise YahooConfigError('Yahoo chart end date must be after start date.')

        try:
            response = self.session.get(
                f'{self.BASE_URL}/{clean_symbol}',
                params={
                    'period1': period1,
                    'period2': period2,
                    'interval': interval,
                    'includePrePost': 'false',
                    'events': 'history',
                },
                timeout=20,
            )
        except requests.RequestException as exc:
            raise YahooConfigError(f'Yahoo request failed: {exc}') from exc

        if response.status_code >= 400:
            raise YahooConfigError(_yahoo_error(response))

        try:
            payload = response.json()
        except ValueError as exc:
            raise YahooConfigError('Yahoo returned a non-JSON chart response.') from exc

        chart = payload.get('chart') or {}
        error = chart.get('error')
        if error:
            description = error.get('description') or error.get('code') or 'Yahoo chart request failed'
            raise YahooConfigError(f'Yahoo chart request failed: {description}')

        result = (chart.get('result') or [None])[0]
        if not result:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

        timestamps = result.get('timestamp') or []
        quote = ((result.get('indicators') or {}).get('quote') or [{}])[0]
        if not timestamps or not quote:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

        data = pd.DataFrame({
            'timestamp': pd.to_datetime(timestamps, unit='s', utc=True).tz_convert(None),
            'open': quote.get('open') or [],
            'high': quote.get('high') or [],
            'low': quote.get('low') or [],
            'close': quote.get('close') or [],
            'volume': quote.get('volume') or [],
        })
        data = data.set_index('timestamp').sort_index()
        return data[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric, errors='coerce').dropna()


def _timeframe_to_interval(timeframe):
    mapping = {
        '1min': '1m',
        '5min': '5m',
        '15min': '15m',
        '1h': '1h',
        '1d': '1d',
    }
    if timeframe not in mapping:
        raise YahooConfigError(f'Unsupported Yahoo timeframe: {timeframe}')
    return mapping[timeframe]


def _to_unix(value, include_full_day=False):
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize('UTC')
    else:
        timestamp = timestamp.tz_convert('UTC')
    if include_full_day and isinstance(value, str) and len(value) <= 10:
        timestamp = timestamp + pd.Timedelta(days=1)
    return int(timestamp.timestamp())


def _yahoo_error(response):
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    chart_error = (payload.get('chart') or {}).get('error') or {}
    message = chart_error.get('description') or response.text[:180] or 'Yahoo chart request failed'
    return f'Yahoo chart request failed ({response.status_code}): {message}'
