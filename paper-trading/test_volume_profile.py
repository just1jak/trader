"""
Test script for Volume Profile and Order Flow Strategy
"""
import pandas as pd
import numpy as np
import sys
import os

# Add the strategies directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'api', 'strategies'))

from volume_profile_orderflow import generate_signals, STRATEGY_INFO

def create_test_data():
    """Create sample OHLCV data for testing"""
    np.random.seed(42)  # For reproducible results
    
    # Create 100 periods of sample data
    n = 100
    
    # Generate price data with some trend and noise
    base_price = 4500  # ES-like price
    returns = np.random.normal(0, 0.01, n)  # 1% volatility
    price = base_price * np.exp(np.cumsum(returns))
    
    # Create OHLCV data
    data = pd.DataFrame()
    data['close'] = price
    data['open'] = price * (1 + np.random.normal(-0.005, 0.005, n))
    data['high'] = np.maximum(data['open'], data['close']) * (1 + np.abs(np.random.normal(0, 0.01, n)))
    data['low'] = np.minimum(data['open'], data['close']) * (1 - np.abs(np.random.normal(0, 0.01, n)))
    data['volume'] = np.random.randint(1000, 5000, n)
    
    # Add approximate buy/sell volume for delta calculation
    # When close > open, more buying pressure; when close < open, more selling pressure
    buying_pressure = np.maximum(0, (data['close'] - data['open']) / data['open'])
    selling_pressure = np.maximum(0, (data['open'] - data['close']) / data['open'])
    
    data['buy_volume'] = (data['volume'] * 0.5 * (1 + buying_pressure)).astype(int)
    data['sell_volume'] = (data['volume'] * 0.5 * (1 + selling_pressure)).astype(int)
    
    return data

def test_strategy():
    """Test the volume profile and order flow strategy"""
    print("Testing Volume Profile and Order Flow Strategy")
    print("=" * 50)
    
    # Create test data
    test_data = create_test_data()
    print(f"Generated {len(test_data)} bars of test data")
    print(f"Price range: {test_data['low'].min():.2f} - {test_data['high'].max():.2f}")
    print(f"Average volume: {test_data['volume'].mean():.0f}")
    
    # Test with default parameters
    default_params = {
        'lookback_period': 20,
        'price_bin_size': 0.25,
        'volume_threshold': 2.0,
        'delta_threshold': 0.5,
        'delta_ma_period': 10,
        'lv_breakout_volume_mult': 1.5
    }
    
    print("\nTesting with default parameters:")
    for param, value in default_params.items():
        print(f"  {param}: {value}")
    
    # Generate signals
    signals = generate_signals(test_data, default_params)
    
    # Analyze results
    long_signals = (signals == 1).sum()
    short_signals = (signals == -1).sum()
    flat_signals = (signals == 0).sum()
    
    print(f"\nSignal Results:")
    print(f"  Long signals: {long_signals}")
    print(f"  Short signals: {short_signals}")
    print(f"  Flat signals: {flat_signals}")
    print(f"  Total signals: {long_signals + short_signals}")
    
    # Show some signal details
    if long_signals > 0 or short_signals > 0:
        signal_indices = np.where(signals != 0)[0]
        print(f"\nFirst few signal indices: {signal_indices[:10]}")
        print(f"Signal values at those indices: {signals.iloc[signal_indices[:10]].values}")
    
    # Test with different parameters
    print("\n" + "=" * 50)
    print("Testing with different parameters:")
    
    # More sensitive parameters
    sensitive_params = default_params.copy()
    sensitive_params['delta_threshold'] = 0.3
    sensitive_params['lv_breakout_volume_mult'] = 1.2
    
    signals_sensitive = generate_signals(test_data, sensitive_params)
    long_sensitive = (signals_sensitive == 1).sum()
    short_sensitive = (signals_sensitive == -1).sum()
    
    print(f"With sensitive parameters (delta_thresh=0.3, vol_mult=1.2):")
    print(f"  Long signals: {long_sensitive}")
    print(f"  Short signals: {short_sensitive}")
    
    # Less sensitive parameters
    strict_params = default_params.copy()
    strict_params['delta_threshold'] = 0.8
    strict_params['lv_breakout_volume_mult'] = 2.0
    
    signals_strict = generate_signals(test_data, strict_params)
    long_strict = (signals_strict == 1).sum()
    short_strict = (signals_strict == -1).sum()
    
    print(f"With strict parameters (delta_thresh=0.8, vol_mult=2.0):")
    print(f"  Long signals: {long_strict}")
    print(f"  Short signals: {short_strict}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_strategy()