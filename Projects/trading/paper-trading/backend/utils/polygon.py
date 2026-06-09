import os

import pandas as pd
import requests
from flask import current_app, has_app_context

from config import Config


class PolygonConfigError(RuntimeError):
    pass


class PolygonClient:
    def __init__(self):
        self.base_url = _setting('POLYGON_BASE_URL', Config.POLYGON_BASE_URL).rstrip('/')
        self.api_key = _setting('POLYGON_API_KEY', Config.POLYGON_API_KEY)
        self.session = requests.Session()

    @property
    def is_configured(self):
        return bool(self.api_key)

    def require_configured(self):
        if not self.is_configured:
            raise PolygonConfigError('Polygon API key is not configured.')

    def get_aggregates(self, symbol, timeframe='1d', start=None, end=None, adjusted=True, limit=5000):
        self.require_configured()
        multiplier, timespan = _timeframe_to_polygon(timeframe)
        start = start or '2025-01-02'
        end = end or start
        clean_symbol = (symbol or 'AAPL').strip().upper()
        url = f'{self.base_url}/v2/aggs/ticker/{clean_symbol}/range/{multiplier}/{timespan}/{start}/{end}'
        try:
            response = self.session.get(
                url,
                params={
                    'adjusted': str(bool(adjusted)).lower(),
                    'sort': 'asc',
                    'limit': int(limit),
                    'apiKey': self.api_key,
                },
                timeout=20,
            )
        except requests.RequestException as exc:
            raise PolygonConfigError(f'Polygon request failed: {exc}') from exc

        if response.status_code >= 400:
            raise PolygonConfigError(_polygon_error(response))

        payload = response.json()
        rows = payload.get('results') or []
        if not rows:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

        data = pd.DataFrame(rows)
        data['timestamp'] = pd.to_datetime(data['t'], unit='ms')
        data.set_index('timestamp', inplace=True)
        data = data.rename(columns={
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume',
        })
        return data[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric, errors='coerce').dropna()


def _timeframe_to_polygon(timeframe):
    mapping = {
        '1min': (1, 'minute'),
        '5min': (5, 'minute'),
        '15min': (15, 'minute'),
        '1h': (1, 'hour'),
        '1d': (1, 'day'),
    }
    if timeframe not in mapping:
        raise PolygonConfigError(f'Unsupported Polygon timeframe: {timeframe}')
    return mapping[timeframe]


def _polygon_error(response):
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    message = payload.get('error') or payload.get('message') or response.text[:180] or 'Polygon request failed'
    return f'Polygon request failed ({response.status_code}): {message}'


def _setting(key, fallback=None):
    if has_app_context():
        return current_app.config.get(key, fallback)
    return os.getenv(key, fallback)
