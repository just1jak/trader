from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[2] / 'data'
TIMEFRAME_RULES = {
    '1min': '1min',
    '5min': '5min',
    '15min': '15min',
    '1h': '1h',
    '1d': '1D',
}


def load_sample_candles(symbol='ES', timeframe='1min', start=None, end=None):
    if symbol.upper() != 'ES':
        raise ValueError('Only ES sample data is available locally.')

    path = DATA_DIR / 'sample_ES_1min.csv'
    if not path.exists():
        raise FileNotFoundError(f'Sample data file not found: {path}')

    data = pd.read_csv(path, parse_dates=['timestamp'])
    data.set_index('timestamp', inplace=True)
    data = _filter_date_range(data, start, end)
    data = _resample(data, timeframe)
    return data


def candles_to_records(data):
    if data.empty:
        return []

    output = data.reset_index().copy()
    output['timestamp'] = output['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    return output.to_dict(orient='records')


def _filter_date_range(data, start, end):
    if start:
        data = data[data.index >= pd.Timestamp(start)]
    if end:
        end_ts = pd.Timestamp(end)
        if isinstance(end, str) and len(end) <= 10:
            end_ts = end_ts + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
        data = data[data.index <= end_ts]
    return data


def _resample(data, timeframe):
    rule = TIMEFRAME_RULES.get(timeframe)
    if rule is None:
        raise ValueError(f'Unsupported timeframe: {timeframe}')
    if rule == '1min':
        return data

    resampled = data.resample(rule).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
    })
    return resampled.dropna()
