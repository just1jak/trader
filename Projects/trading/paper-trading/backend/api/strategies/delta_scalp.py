import pandas as pd
import numpy as np

def generate_signals(data: pd.DataFrame, params: dict):
    """
    Order‑Flow Imbalance (Delta) Scalping.
    Requires delta column: buying volume - selling volume.
    If not present, approximate delta as (close - open) * volume as proxy.
    Parameters: {'delta_threshold': float, 'delta_ma_period': int}
    """
    # Proxy delta if not provided
    if 'delta' in data.columns:
        delta = data['delta']
    else:
        # Approximate: price change times volume
        delta = (data['close'] - data['open']) * data['volume']
    # Smooth delta
    ma_period = params.get('delta_ma_period', 10)
    delta_ma = delta.rolling(window=ma_period, min_periods=1).mean()
    # Normalize by volume to get intensity
    vol_ma = data['volume'].rolling(window=ma_period, min_periods=1).mean()
    delta_norm = delta_ma / vol_ma.replace(0, np.nan)
    threshold = params.get('delta_threshold', 0.5)
    signals = pd.Series(0, index=data.index)
    signals[delta_norm > threshold] = 1   # buying pressure -> long
    signals[delta_norm < -threshold] = -1 # selling pressure -> short
    return signals