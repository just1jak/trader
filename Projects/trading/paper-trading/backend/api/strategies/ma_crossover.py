import pandas as pd

def generate_signals(data: pd.DataFrame, params: dict):
    """
    Moving average crossover strategy.
    params: {'fast': int, 'slow': int}
    Returns a pandas Series with index matching data, values: 1 (long), -1 (short), 0 (flat)
    """
    fast = params.get('fast', 9)
    slow = params.get('slow', 21)
    
    # Calculate moving averages
    data = data.copy()
    data['ma_fast'] = data['close'].rolling(window=fast, min_periods=1).mean()
    data['ma_slow'] = data['close'].rolling(window=slow, min_periods=1).mean()
    
    # Generate signals
    signals = pd.Series(0, index=data.index)
    signals[data['ma_fast'] > data['ma_slow']] = 1   # long
    signals[data['ma_fast'] < data['ma_slow']] = -1  # short
    
    # To avoid switching too frequently, we can require the crossover to persist for one bar.
    # But for simplicity, we'll leave as is.
    return signals