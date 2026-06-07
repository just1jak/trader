import json
import datetime
import statistics
import os

# Mapping from stock tickers to futures symbols (example)
# In reality, you would need a more sophisticated mapping or model.
TICKER_TO_FUTURES = {
    'AAPL': 'ES=F',  # S&P 500 futures (as a proxy for large-cap tech)
    'MSFT': 'ES=F',
    'GOOGL': 'ES=F',
    'AMZN': 'ES=F',
    'TSLA': 'ES=F',
    # Add more as needed
}

def load_trades(filepath):
    """
    Load trades from a JSON file.
    """
    if not os.path.exists(filepath):
        print(f"File {filepath} not found.")
        return []
    with open(filepath, 'r') as f:
        trades = json.load(f)
    return trades

def get_futures_symbol(ticker):
    """
    Map a stock ticker to a futures symbol.
    Returns the futures symbol or None if not found.
    """
    return TICKER_TO_FUTURES.get(ticker.upper())

def fetch_futures_data(symbol, start_date, end_date):
    """
    Placeholder function to simulate fetching futures data.
    In a real implementation, this would call an API or read from a database.
    For now, we generate deterministic placeholder data based on the symbol and date range.
    Returns a list of dictionaries with keys: 'date', 'open', 'high', 'low', 'close', 'volume'.
    """
    # Convert string dates to datetime objects for calculation
    try:
        start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        print(f"Invalid date format: {start_date} or {end_date}")
        return []

    # Ensure we look at least a few days to capture business days
    # If start date is weekend, move to next Monday
    if start.weekday() == 5:  # Saturday
        start = start + datetime.timedelta(days=2)
    elif start.weekday() == 6:  # Sunday
        start = start + datetime.timedelta(days=1)
    
    # Ensure end date is at least start date
    if end < start:
        end = start

    # Generate a list of business days (skip weekends) between start and end inclusive
    current = start
    data = []
    while current <= end:
        # Skip Saturday (5) and Sunday (6)
        if current.weekday() < 5:
            # Generate deterministic but varying prices based on symbol and date
            # Use a simple hash of the symbol and date to get a seed
            seed = hash(symbol + current.strftime('%Y-%m-%d')) % 1000
            # Base price different for each symbol to simulate different futures
            base_price = 4000  # base for ES
            if 'CL' in symbol:  # Crude Oil
                base_price = 80
            elif 'GC' in symbol:  # Gold
                base_price = 2000
            elif 'SI' in symbol:  # Silver
                base_price = 25
            # Add some deterministic variation
            variation = (seed % 200) - 100  # -100 to +100
            price = base_price + variation
            # Generate OHLC around this price
            open_price = price * (0.99 + (seed % 2) * 0.02)  # either 0.99 or 1.01
            high_price = price * (1.0 + (seed % 3) * 0.01)   # 1.0, 1.01, or 1.02
            low_price = price * (0.99 - (seed % 3) * 0.01)   # 0.99, 0.98, or 0.97
            close_price = price * (0.995 + (seed % 3) * 0.005) # between 0.995 and 1.005
            volume = 1000 + (seed % 10000)
            data.append({
                'date': current.strftime('%Y-%m-%d'),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
        current += datetime.timedelta(days=1)
    return data

def calculate_trade_return(trade, holding_days=1):
    """
    Calculate the return for a single trade based on futures price movement.
    """
    ticker = trade.get('ticker')
    if not ticker:
        print("Trade missing ticker")
        return None

    futures_symbol = get_futures_symbol(ticker)
    if not futures_symbol:
        print(f"No futures mapping for ticker {ticker}")
        return None

    # Parse transaction date
    try:
        transaction_date = datetime.datetime.strptime(trade['transaction_date'], '%Y-%m-%d')
    except Exception as e:
        print(f"Error parsing transaction_date {trade.get('transaction_date')}: {e}")
        return None

    # Define the period for which we need futures data
    start_date = transaction_date.strftime('%Y-%m-%d')
    end_date = (transaction_date + datetime.timedelta(days=holding_days)).strftime('%Y-%m-%d')

    # Fetch futures data (placeholder)
    data = fetch_futures_data(futures_symbol, start_date, end_date)
    if not data:
        print(f"Could not fetch futures data for {futures_symbol} from {start_date} to {end_date}")
        return None

    # We assume we enter at the close of the transaction date and exit at the close of the last day
    # Find the entry price (close on transaction_date or next available)
    entry_price = None
    for day in data:
        if day['date'] >= start_date:
            entry_price = day['close']
            break
    if entry_price is None:
        # If no data on or after start_date, use the last available
        entry_price = data[-1]['close'] if data else None
    if entry_price is None:
        print(f"Could not determine entry price for {futures_symbol} on or after {start_date}")
        return None

    # Find the exit price (close on exit_date or last available)
    exit_date = transaction_date + datetime.timedelta(days=holding_days)
    exit_date_str = exit_date.strftime('%Y-%m-%d')
    exit_price = None
    for day in data:
        if day['date'] >= exit_date_str:
            exit_price = day['close']
            break
    if exit_price is None:
        # If no data on or after exit_date, use the last available
        exit_price = data[-1]['close'] if data else None
    if exit_price is None:
        print(f"Could not determine exit price for {futures_symbol} on or after {exit_date_str}")
        return None

    # Calculate return (assuming long position for purchase, short for sale?)
    transaction_type = trade.get('transaction_type', '').lower()
    if 'purchase' in transaction_type:
        # Long: profit if price goes up
        ret = (exit_price - entry_price) / entry_price
    elif 'sale' in transaction_type:
        # Short: profit if price goes down
        ret = (entry_price - exit_price) / entry_price
    else:
        # Default to long
        ret = (exit_price - entry_price) / entry_price

    return ret

def run_backtest(holding_days=1):
    """
    Run the backtest on all available trades.
    """
    # Load House and Senate trades
    house_trades = load_trades('house_trades.json')
    senate_trades = load_trades('senate_trades.json')
    all_trades = house_trades + senate_trades

    if not all_trades:
        print("No trades to backtest.")
        return None

    returns = []
    trade_details = []

    for trade in all_trades:
        ret = calculate_trade_return(trade, holding_days=holding_days)
        if ret is not None:
            returns.append(ret)
            trade_details.append({
                'ticker': trade.get('ticker'),
                'transaction_date': trade.get('transaction_date'),
                'member': trade.get('member'),
                'transaction_type': trade.get('transaction_type'),
                'return': ret
            })

    if not returns:
        print("No valid returns calculated.")
        return None

    # Calculate statistics using built-in functions and statistics module
    total_return = sum(returns)
    avg_return = statistics.mean(returns) if returns else 0
    try:
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0
    except statistics.StatisticsError:
        std_return = 0
    sharpe = avg_return / std_return if std_return != 0 else 0
    win_rate = sum(1 for r in returns if r > 0) / len(returns) if returns else 0

    results = {
        'total_trades': len(returns),
        'total_return': total_return,
        'average_return': avg_return,
        'return_std': std_return,
        'sharpe_ratio': sharpe,
        'win_rate': win_rate,
        'trade_details': trade_details
    }

    return results

if __name__ == "__main__":
    print("Running Congressional Trading Backtest...")
    results = run_backtest(holding_days=1)
    if results:
        print("\n=== Backtest Results ===")
        print(f"Total Trades: {results['total_trades']}")
        print(f"Total Return: {results['total_return']:.2%}")
        print(f"Average Return: {results['average_return']:.2%}")
        print(f"Return Std: {results['return_std']:.2%}")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"Win Rate: {results['win_rate']:.2%}")
        print("\n=== Trade Details (first 5) ===")
        for trade in results['trade_details'][:5]:
            print(f"{trade['transaction_date']} {trade['member']} {trade['ticker']} {trade['transaction_type']}: {trade['return']:.2%}")
    else:
        print("Backtest failed to produce results.")