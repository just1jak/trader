import pandas as pd

def generate_signals(data: pd.DataFrame, params: dict):
    """
    Opening Range Breakout (ORB) strategy.
    Parameters: {'orb_minutes': int, 'breakout_mult': float}
    """
    orb_minutes = params.get('orb_minutes', 30)
    breakout_mult = params.get('breakout_mult', 0.5)
    # Determine session open: assume data starts at session open for simplicity
    # In production, you'd need to detect session boundaries.
    high = data['high'].rolling(window=orb_minutes).max()
    low = data['low'].rolling(window=orb_minutes).min()
    # Use prior orb high/low (shift to avoid lookahead)
    orb_high = high.shift(1)
    orb_low = low.shift(1)
    # ATR-like range for filter
    atr = (data['high'] - data['low']).rolling(window=14).mean().shift(1)
    signals = pd.Series(0, index=data.index)
    signals[(data['close'] > orb_high + breakout_mult * atr)] = 1
    signals[(data['close'] < orb_low - breakout_mult * atr)] = -1
    return signals