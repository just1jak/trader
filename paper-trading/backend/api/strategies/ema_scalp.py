import pandas as pd

def generate_signals(data: pd.DataFrame, params: dict):
    """
    Micro‑Trend EMA Scalping.
    Parameters: {'fast': int, 'slow': int, 'max_hold_bars': int}
    """
    fast = params.get('fast', 3)
    slow = params.get('slow', 8)
    max_hold = params.get('max_hold_bars', 5)
    ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
    raw = pd.Series(0, index=data.index)
    raw[ema_fast > ema_slow] = 1
    raw[ema_fast < ema_slow] = -1
    # Apply max hold: flatten after max_hold bars in same direction
    signal = pd.Series(0, index=data.index)
    position = 0
    bars_in_position = 0
    for idx in range(len(data)):
        if position == 0:
            if raw.iloc[idx] == 1:
                position = 1
                bars_in_position = 0
            elif raw.iloc[idx] == -1:
                position = -1
                bars_in_position = 0
        else:
            bars_in_position += 1
            if bars_in_position >= max_hold:
                position = 0
                bars_in_position = 0
            elif position == 1 and raw.iloc[idx] == -1:
                position = -1
                bars_in_position = 0
            elif position == -1 and raw.iloc[idx] == 1:
                position = 1
                bars_in_position = 0
        signal.iloc[idx] = position
    return signal