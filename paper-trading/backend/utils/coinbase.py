import pandas as pd
import requests


class CoinbaseConfigError(RuntimeError):
    pass


class CoinbaseClient:
    BASE_URL = 'https://api.exchange.coinbase.com'

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})

    def get_candles(self, product_id='BTC-USD', timeframe='1d', start=None, end=None):
        granularity = _timeframe_to_granularity(timeframe)
        clean_product = (product_id or 'BTC-USD').strip().upper()
        start_ts = _to_utc_timestamp(start or '2025-01-02')
        end_ts = _to_utc_timestamp(end or start or '2025-01-10')
        _validate_range(start_ts, end_ts, granularity)

        response = self.session.get(
            f'{self.BASE_URL}/products/{clean_product}/candles',
            params={
                'granularity': granularity,
                'start': start_ts.isoformat().replace('+00:00', 'Z'),
                'end': end_ts.isoformat().replace('+00:00', 'Z'),
            },
            timeout=20,
        )
        if response.status_code >= 400:
            raise CoinbaseConfigError(_coinbase_error(response))

        try:
            rows = response.json()
        except ValueError as exc:
            raise CoinbaseConfigError('Coinbase returned a non-JSON candle response.') from exc

        if not rows:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        if not isinstance(rows, list):
            raise CoinbaseConfigError('Coinbase candle response was not a list.')

        data = pd.DataFrame(rows, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
        data['timestamp'] = pd.to_datetime(data['time'], unit='s', utc=True).dt.tz_convert(None)
        data = data.set_index('timestamp').sort_index()
        return data[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric, errors='coerce').dropna()


def _timeframe_to_granularity(timeframe):
    mapping = {
        '1min': 60,
        '5min': 300,
        '15min': 900,
        '1h': 3600,
        '1d': 86400,
    }
    if timeframe not in mapping:
        raise CoinbaseConfigError(f'Unsupported Coinbase timeframe: {timeframe}')
    return mapping[timeframe]


def _to_utc_timestamp(value):
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize('UTC')
    else:
        timestamp = timestamp.tz_convert('UTC')
    return timestamp


def _validate_range(start, end, granularity):
    if end < start:
        raise CoinbaseConfigError('Coinbase candle end date must be on or after start date.')
    candle_count = max(1, (end - start).total_seconds() / granularity)
    if candle_count > 300:
        raise CoinbaseConfigError(
            'Coinbase returns at most 300 candles per request. Shorten the date range or use a larger timeframe.'
        )


def _coinbase_error(response):
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    message = payload.get('message') or response.text[:180] or 'Coinbase request failed'
    return f'Coinbase request failed ({response.status_code}): {message}'
