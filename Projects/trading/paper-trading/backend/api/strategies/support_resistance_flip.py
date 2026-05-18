import pandas as pd
import numpy as np

def generate_signals(data: pd.DataFrame, params: dict):
    """
    Support/Resistance Flip Scalping.
    Parameters: {'lookback': int, 'retest_tolerance': float}
    Detects swing highs/lows, then price breaks and retests as opposite.
    Simple implementation: compute rolling max/min, breakout, then retest within tolerance.
    """
    lookback = params.get('lookback', 20)
    tol = params.get('retest_tolerance', 0.5)  # in price units (e.g., ticks)
    # Rolling max/min of high/low
    roll_high = data['high'].rolling(window=lookback, min_periods=1).max()
    roll_low = data['low'].rolling(window=lookback, min_periods=1).min()
    # Identify breakout above recent high or below recent low
    breakout_up = (data['close'] > roll_high.shift(1)) & (data['close'].shift(1) <= roll_high.shift(2))
    breakout_dn = (data['close'] < roll_low.shift(1)) & (data['close'].shift(1) >= roll_low.shift(2))
    # After breakout, wait for retest within tolerance of the broken level
    signal = pd.Series(0, index=data.index)
    position = 0
    # Track the level we are waiting to retest
    target_level = None
    target_type = None  # 'support' or 'resistance'
    for i in range(len(data)):
        if position == 0:
            # Look for breakout
            if breakout_up.iloc[i]:
                # Bullish breakout: wait for retest of old resistance (now support)
                target_level = roll_high.iloc[i-1] if i>0 else roll_high.iloc[i]
                target_type = 'support'  # we expect price to come back to this level as support
                position = 1  # go long
            elif breakout_dn.iloc[i]:
                # Bearish breakout: wait for retest of old support (now resistance)
                target_level = roll_low.iloc[i-1] if i>0 else roll_low.iloc[i]
                target_type = 'resistance'
                position = -1  # go short
        else:
            # In a position, check if price has retraced to target level within tolerance
            if position == 1:  # long, waiting for support retest
                if abs(data['low'].iloc[i] - target_level) <= tol:
                    # Retest found, keep long
                    pass
                else:
                    # If price moves away without retest, exit
                    position = 0
                    target_level = None
            elif position == -1:  # short, waiting for resistance retest
                if abs(data['high'].iloc[i] - target_level) <= tol:
                    # Retest found, keep short
                    pass
                else:
                    position = 0
                    target_level = None
        signal.iloc[i] = position
    return signal