import pandas as pd
import numpy as np
import importlib
import os

def run_backtest(data: pd.DataFrame, strategy_name: str, params: dict):
    """
    Run a backtest on the given data using the specified strategy.
    data: DataFrame with datetime index and columns ['open','high','low','close','volume']
    strategy_name: name of the strategy module (without .py) in backend/api/strategies/
    params: dictionary of parameters for the strategy
    Returns a dict with equity curve, trades, and performance metrics.
    """
    # Load the strategy module dynamically
    try:
        strategy_module = importlib.import_module(f'api.strategies.{strategy_name}')
    except ImportError as e:
        raise ValueError(f"Strategy '{strategy_name}' not found.") from e

    # Ensure the strategy has a generate_signals function
    if not hasattr(strategy_module, 'generate_signals'):
        raise ValueError(f"Strategy '{strategy_name}' must define a generate_signals function.")

    # Generate signals
    signals = strategy_module.generate_signals(data, params)
    # signals should be a Series with index matching data, values: 1 (long), -1 (short), 0 (flat)

    # Align signals with data
    signals = signals.reindex(data.index).fillna(0)

    # Simple backtest: assume we enter at the open of the next bar after signal
    # and exit when signal changes or at the end.
    # We'll calculate returns based on close-to-close for simplicity.
    # For a more realistic backtest, you'd need to consider slippage, commissions, etc.

    # Calculate returns: daily (or per period) return of the asset
    data['returns'] = data['close'].pct_change().fillna(0)

    # Strategy returns: we are long when signal == 1, short when signal == -1, flat otherwise.
    # We'll assume we can reverse instantly (no delay) and that we earn the asset's return when long,
    # and lose the asset's return when short (i.e., we short the asset).
    data['strategy_returns'] = (data['returns'] * signals.shift(1)).fillna(0)  # shift to avoid lookahead

    # Calculate cumulative returns
    data['cumulative_returns'] = (1 + data['strategy_returns']).cumprod()
    data['buy_hold_returns'] = (1 + data['returns']).cumprod()

    # Performance metrics
    total_return = data['cumulative_returns'].iloc[-1] - 1
    buy_hold_total_return = data['buy_hold_returns'].iloc[-1] - 1

    # Sharpe ratio (assuming 252 trading days per year, adjust if needed for intraday)
    # For simplicity, we'll use the sample Sharpe (not annualized) and note the frequency.
    # For intraday, you'd want to annualize by sqrt(252*number_of_periods_per_day)
    # We'll leave it as is for now.
    strategy_std = data['strategy_returns'].std()
    sharpe = 0 if strategy_std == 0 or np.isnan(strategy_std) else data['strategy_returns'].mean() / strategy_std * np.sqrt(252)

    # Max drawdown
    roll_max = data['cumulative_returns'].cummax()
    drawdown = (data['cumulative_returns'] - roll_max) / roll_max
    max_drawdown = drawdown.min()

    # Win rate (percentage of periods where strategy_returns > 0)
    win_rate = (data['strategy_returns'] > 0).sum() / len(data['strategy_returns'])

    # Extract trades (simplified: when signal changes)
    data['signal_change'] = signals.diff().fillna(0)
    # Entry when signal changes from 0 to +/-1, exit when signal changes to 0 or to opposite sign.
    # We'll just mark entries and exits for simplicity.
    entries = data[data['signal_change'] != 0].copy()
    entries['entry_signal'] = signals.loc[entries.index]
    # For each entry, we assume exit at the next signal change or end of data.
    # This is a simplified trade list.

    trades = []
    position = 0
    entry_price = None
    entry_time = None
    for idx, row in data.iterrows():
        if position == 0 and signals.loc[idx] != 0:
            # Enter position
            position = signals.loc[idx]
            entry_price = row['open']  # assume we enter at open of this bar
            entry_time = idx
        elif position != 0 and signals.loc[idx] == 0:
            # Exit position (flat)
            exit_price = row['close']  # assume we exit at close of this bar
            pnl = (exit_price - entry_price) * position  # for long: + if up, short: + if down
            trades.append({
                'entry_time': entry_time,
                'exit_time': idx,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'position': position,
                'pnl': pnl,
                'return': pnl / (abs(entry_price) * 1)  # simplified, assuming 1 contract
            })
            position = 0
            entry_price = None
            entry_time = None
        elif position != 0 and signals.loc[idx] != 0 and signals.loc[idx] != position:
            # Reverse position
            exit_price = row['close']
            pnl = (exit_price - entry_price) * position
            trades.append({
                'entry_time': entry_time,
                'exit_time': idx,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'position': position,
                'pnl': pnl,
                'return': pnl / (abs(entry_price) * 1)
            })
            # Enter new position immediately
            position = signals.loc[idx]
            entry_price = row['open']
            entry_time = idx

    # If still in position at the end, exit at last close
    if position != 0:
        exit_price = data.iloc[-1]['close']
        pnl = (exit_price - entry_price) * position
        trades.append({
            'entry_time': entry_time,
            'exit_time': data.index[-1],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'position': position,
            'pnl': pnl,
            'return': pnl / (abs(entry_price) * 1)
        })

    # Prepare results
    results = {
        'equity_curve': data['cumulative_returns'].reset_index().rename(columns={'index': 'timestamp', 'cumulative_returns': 'equity'}).to_dict(orient='records'),
        'buy_hold_curve': data['buy_hold_returns'].reset_index().rename(columns={'index': 'timestamp', 'buy_hold_returns': 'equity'}).to_dict(orient='records'),
        'trades': trades,
        'metrics': {
            'total_return': total_return,
            'buy_hold_total_return': buy_hold_total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(trades),
            'net_profit': sum(t['pnl'] for t in trades)
        }
    }
    return results
