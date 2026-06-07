import pandas as pd


def run_long_option_backtest(
    data: pd.DataFrame,
    option_type: str,
    strike: float,
    premium: float,
    contracts: int = 1,
    multiplier: int = 100,
    strategy: str = None,
    short_strike: float = None,
    short_premium: float = 0,
):
    """
    Simulation-only long call/put payoff proxy using underlying closes.

    This is not historical option pricing. It estimates contract value from
    intrinsic value at each underlying close and the supplied entry premium.
    """
    if data.empty:
        raise ValueError('No underlying data supplied for options backtest.')

    option_type = option_type.upper()
    strategy = (strategy or ('long_call' if option_type == 'CALL' else 'long_put')).lower()
    if option_type not in {'CALL', 'PUT'}:
        raise ValueError('option_type must be CALL or PUT.')
    if strike <= 0:
        raise ValueError('strike must be greater than zero.')
    if premium < 0:
        raise ValueError('premium cannot be negative.')
    if short_premium < 0:
        raise ValueError('short_premium cannot be negative.')
    if contracts <= 0:
        raise ValueError('contracts must be greater than zero.')

    close = data['close'].astype(float)
    intrinsic, debit, strategy_label = _strategy_value(
        close=close,
        option_type=option_type,
        strike=strike,
        premium=premium,
        strategy=strategy,
        short_strike=short_strike,
        short_premium=short_premium,
    )
    if debit <= 0:
        raise ValueError('Net premium/debit must be greater than zero for this options simulator.')

    entry_cost = debit * multiplier * contracts
    value = intrinsic * multiplier * contracts
    pnl = value - entry_cost
    equity = entry_cost + pnl
    returns = equity.pct_change().replace([float('inf'), float('-inf')], 0).fillna(0)

    total_return = (equity.iloc[-1] - entry_cost) / entry_cost if entry_cost else 0
    max_drawdown = _max_drawdown(equity)
    win_rate = float((pnl > 0).sum() / len(pnl))
    sharpe = _safe_sharpe(returns)

    curve = pd.DataFrame({
        'timestamp': data.index,
        'equity': equity,
        'pnl': pnl,
        'intrinsic_value': intrinsic,
        'underlying_close': close,
    }).reset_index(drop=True)
    curve['timestamp'] = pd.to_datetime(curve['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

    entry_time = data.index[0]
    exit_time = data.index[-1]
    trades = [{
        'entry_time': entry_time.isoformat() if hasattr(entry_time, 'isoformat') else str(entry_time),
        'exit_time': exit_time.isoformat() if hasattr(exit_time, 'isoformat') else str(exit_time),
        'strategy': strategy,
        'strategy_label': strategy_label,
        'option_type': option_type,
        'strike': strike,
        'short_strike': short_strike,
        'premium': premium,
        'short_premium': short_premium,
        'contracts': contracts,
        'entry_cost': entry_cost,
        'exit_value': float(value.iloc[-1]),
        'pnl': float(pnl.iloc[-1]),
        'return': float(total_return),
    }]

    return {
        'equity_curve': curve.to_dict(orient='records'),
        'trades': trades,
        'metrics': {
            'total_return': float(total_return),
            'sharpe_ratio': float(sharpe),
            'max_drawdown': float(max_drawdown),
            'win_rate': win_rate,
            'total_trades': 1,
            'net_profit': float(pnl.iloc[-1]),
            'entry_cost': float(entry_cost),
        },
        'assumptions': [
            f'Simulation-only {strategy_label} payoff proxy.',
            'Uses underlying close and intrinsic value, not historical option bid/ask candles or greeks.',
            'Does not model implied volatility, theta decay, assignment, early exercise, liquidity, or slippage.',
        ],
    }


def _strategy_value(close, option_type, strike, premium, strategy, short_strike=None, short_premium=0):
    if strategy == 'long_call':
        return (close - strike).clip(lower=0), premium, 'long call'
    if strategy == 'long_put':
        return (strike - close).clip(lower=0), premium, 'long put'
    if strategy == 'long_straddle':
        call_value = (close - strike).clip(lower=0)
        put_value = (strike - close).clip(lower=0)
        return call_value + put_value, premium, 'long straddle'
    if strategy == 'bull_call_spread':
        if short_strike is None or short_strike <= strike:
            raise ValueError('bull_call_spread requires short_strike above strike.')
        long_value = (close - strike).clip(lower=0)
        short_value = (close - float(short_strike)).clip(lower=0)
        return long_value - short_value, premium - short_premium, 'bull call spread'
    if strategy == 'bear_put_spread':
        if short_strike is None or short_strike >= strike:
            raise ValueError('bear_put_spread requires short_strike below strike.')
        long_value = (strike - close).clip(lower=0)
        short_value = (float(short_strike) - close).clip(lower=0)
        return long_value - short_value, premium - short_premium, 'bear put spread'

    if option_type == 'CALL':
        return (close - strike).clip(lower=0), premium, 'long call'
    return (strike - close).clip(lower=0), premium, 'long put'


def _max_drawdown(series):
    running_max = series.cummax()
    drawdown = (series - running_max) / running_max.replace(0, pd.NA)
    return drawdown.min() if not drawdown.empty else 0


def _safe_sharpe(returns):
    std = returns.std()
    if not std or pd.isna(std):
        return 0
    return returns.mean() / std
