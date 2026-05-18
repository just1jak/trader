"""
Volume Profile and Order Flow Strategy
Combines volume profile analysis with order flow metrics to identify
high-probability breakout and reversal zones.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def generate_signals(data: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
    """
    Generate trading signals based on volume profile and order flow analysis.
    
    Parameters:
    -----------
    data : pd.DataFrame
        OHLCV data with columns: ['open', 'high', 'low', 'close', 'volume']
        Optionally includes: 'buy_volume', 'sell_volume' for direct delta calculation
    params : dict
        Strategy parameters:
        - lookback_period: int (default 20)
        - price_bin_size: float (default 0.25 for ES)
        - volume_threshold: float (default 2.0)
        - delta_threshold: float (default 0.5)
        - delta_ma_period: int (default 10)
        - lv_breakout_volume_mult: float (default 1.5)
        
    Returns:
    --------
    pd.Series
        Signals: 1 (long), -1 (short), 0 (flat)
    """
    
    # Set default parameters
    lookback_period = params.get('lookback_period', 20)
    price_bin_size = params.get('price_bin_size', 0.25)
    volume_threshold = params.get('volume_threshold', 2.0)
    delta_threshold = params.get('delta_threshold', 0.5)
    delta_ma_period = params.get('delta_ma_period', 10)
    lv_breakout_volume_mult = params.get('lv_breakout_volume_mult', 1.5)
    
    # Initialize signals series
    signals = pd.Series(0, index=data.index)
    
    # Calculate delta (buying vs selling pressure)
    if 'buy_volume' in data.columns and 'sell_volume' in data.columns:
        # Direct delta calculation from time/sales
        delta = data['buy_volume'] - data['sell_volume']
    else:
        # Approximate delta from price change and volume
        delta = (data['close'] - data['open']) * data['volume']
    
    # Smoothed delta for signal generation
    delta_ma = delta.rolling(window=delta_ma_period, min_periods=1).mean()
    
    # Normalize delta by average volume for threshold comparison
    avg_volume = data['volume'].rolling(window=lookback_period, min_periods=1).mean()
    normalized_delta = delta_ma / avg_volume.replace(0, np.nan)
    
    # Calculate volume profile for each lookback period
    # We'll calculate it rolling, but for simplicity in this implementation,
    # we'll use a simplified approach focusing on recent volume clusters
    
    for i in range(lookback_period, len(data)):
        # Get lookback window
        window_data = data.iloc[i-lookback_period:i]
        current_price = data.iloc[i]['close']
        current_volume = data.iloc[i]['volume']
        current_normalized_delta = normalized_delta.iloc[i]
        
        # Skip if we don't have enough data for volume calculations
        if pd.isna(current_normalized_delta) or pd.isna(avg_volume.iloc[i]):
            continue
            
        # Calculate volume-weighted price bins for the lookback period
        price_min = window_data['low'].min()
        price_max = window_data['high'].max()
        
        # Create price bins
        bin_edges = np.arange(price_min, price_max + price_bin_size, price_bin_size)
        if len(bin_edges) < 2:
            continue
            
        # Initialize volume profile
        volume_profile = np.zeros(len(bin_edges) - 1)
        
        # Distribute volume to price bins (simplified approach)
        # In a real implementation, you'd use time/sales data for exact distribution
        for j in range(len(window_data)):
            # Distribute each bar's volume across its price range
            bar_low = window_data.iloc[j]['low']
            bar_high = window_data.iloc[j]['high']
            bar_volume = window_data.iloc[j]['volume']
            
            # Find which bins this bar spans
            low_bin = max(0, int((bar_low - price_min) / price_bin_size))
            high_bin = min(len(volume_profile) - 1, int((bar_high - price_min) / price_bin_size))
            
            # Distribute volume evenly across spanned bins
            if high_bin >= low_bin:
                volume_per_bin = bar_volume / (high_bin - low_bin + 1)
                for k in range(low_bin, high_bin + 1):
                    volume_profile[k] += volume_per_bin
        
        # Calculate average bin volume for threshold
        avg_bin_volume = np.mean(volume_profile) if np.sum(volume_profile) > 0 else 0
        
        # Identify significant volume nodes
        high_volume_threshold = avg_bin_volume * volume_threshold
        low_volume_threshold = avg_bin_volume * 0.3  # LVN threshold
        
        # Find HVNs and LVNs
        hvn_bins = np.where(volume_profile >= high_volume_threshold)[0]
        lvn_bins = np.where(volume_profile <= low_volume_threshold)[0]
        
        if len(hvn_bins) == 0 or len(lvn_bins) == 0:
            continue
            
        # Convert bin indices to price levels
        hvn_prices = price_min + (hvn_bins + 0.5) * price_bin_size
        lvn_prices = price_min + (lvn_bins + 0.5) * price_bin_size
        
        # Calculate POC (Point of Control) - price with maximum volume
        poc_bin = np.argmax(volume_profile)
        poc_price = price_min + (poc_bin + 0.5) * price_bin_size
        
        # Calculate Value Area (simplified - ~70% of volume around POC)
        # Sort bins by volume descending and accumulate until ~70% reached
        sorted_indices = np.argsort(volume_profile)[::-1]  # Descending order
        cumulative_volume = 0
        total_volume = np.sum(volume_profile)
        va_bins = []
        
        for idx in sorted_indices:
            va_bins.append(idx)
            cumulative_volume += volume_profile[idx]
            if cumulative_volume >= 0.7 * total_volume:
                break
        
        if len(va_bins) > 0:
            va_prices = price_min + (np.array(va_bins) + 0.5) * price_bin_size
            vah = np.max(va_prices)  # Value Area High
            val = np.min(va_prices)  # Value Area Low
        else:
            vah = val = poc_price
        
        # === SIGNAL GENERATION ===
        
        # 1. LVN Breakout Signals
        # Check if current price is near any LVN (within half bin size)
        near_lvn = False
        lvn_side = 0  # 1 for above LVN (long bias), -1 for below LVN (short bias)
        
        for lvn_price in lvn_prices:
            distance_to_lvn = abs(current_price - lvn_price)
            if distance_to_lvn <= price_bin_size:
                near_lvn = True
                # Determine if price is above or below the LVN
                if current_price > lvn_price:
                    lvn_side = 1  # Above LVN - potential long breakout
                else:
                    lvn_side = -1  # Below LVN - potential short breakout
                break
        
        # Volume confirmation for breakout
        volume_confirmed = current_volume > (avg_volume.iloc[i] * lv_breakout_volume_mult)
        
        # Order flow confirmation
        delta_long_signal = current_normalized_delta > delta_threshold
        delta_short_signal = current_normalized_delta < -delta_threshold
        
        # LVN Breakout Long
        if (near_lvn and lvn_side == 1 and volume_confirmed and 
            delta_long_signal and current_price > poc_price):
            signals.iloc[i] = 1
            
        # LVN Breakout Short
        elif (near_lvn and lvn_side == -1 and volume_confirmed and 
              delta_short_signal and current_price < poc_price):
            signals.iloc[i] = -1
            
        # 2. POC Rejection/Rachet Signals
        # Test if price is rejecting POC with order flow absorption
        poc_distance = abs(current_price - poc_price)
        near_poc = poc_distance <= (price_bin_size * 2)  # Within 2 bins of POC
        
        # Long signal: Price testing POC from below with buying absorption
        if (near_poc and current_price >= poc_price and 
            delta_long_signal and 
            data.iloc[i]['close'] > data.iloc[i]['open']):  # Bullish candle
            signals.iloc[i] = 1
            
        # Short signal: Price testing POC from above with selling absorption
        elif (near_poc and current_price <= poc_price and 
              delta_short_signal and 
              data.iloc[i]['close'] < data.iloc[i]['open']):  # Bearish candle
            signals.iloc[i] = -1
            
        # 3. Value Area Extremes (fade signals)
        # Only consider if we're well outside the VA with contrary order flow
        if current_price > vah and current_normalized_delta < -delta_threshold * 0.5:
            # Above VA with selling pressure - potential short fade
            signals.iloc[i] = -1
        elif current_price < val and current_normalized_delta > delta_threshold * 0.5:
            # Below VA with buying pressure - potential long fade
            signals.iloc[i] = 1
    
    return signals


# Strategy metadata
STRATEGY_INFO = {
    'name': 'Volume Profile and Order Flow',
    'description': 'Combines volume profile analysis with order flow metrics to identify high-probability breakout and reversal zones.',
    'parameters': {
        'lookback_period': {
            'type': 'int',
            'default': 20,
            'min': 5,
            'max': 100,
            'description': 'Number of bars for volume profile calculation'
        },
        'price_bin_size': {
            'type': 'float',
            'default': 0.25,
            'min': 0.01,
            'max': 10.0,
            'description': 'Tick size for volume binning (0.25 for ES futures)'
        },
        'volume_threshold': {
            'type': 'float',
            'default': 2.0,
            'min': 1.0,
            'max': 5.0,
            'description': 'Minimum volume for significant node (x average bin volume)'
        },
        'delta_threshold': {
            'type': 'float',
            'default': 0.5,
            'min': 0.1,
            'max': 2.0,
            'description': 'Threshold for normalized delta signal'
        },
        'delta_ma_period': {
            'type': 'int',
            'default': 10,
            'min': 2,
            'max': 50,
            'description': 'Smoothing period for delta calculation'
        },
        'lv_breakout_volume_mult': {
            'type': 'float',
            'default': 1.5,
            'min': 1.0,
            'max': 3.0,
            'description': 'Volume confirmation multiplier for LVN breaks'
        }
    }
}

if __name__ == "__main__":
    # Example usage for testing
    print("Volume Profile and Order Flow Strategy")
    print("=" * 50)
    print(f"Strategy: {STRATEGY_INFO['name']}")
    print(f"Description: {STRATEGY_INFO['description']}")
    print("\nParameters:")
    for param, info in STRATEGY_INFO['parameters'].items():
        print(f"  {param}: {info['default']} ({info['description']})")