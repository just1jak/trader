import sys
from pathlib import Path

import pandas as pd


BACKEND = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND))

from api.strategies.riley_coleman_reversal import generate_signals, STRATEGY_INFO
from utils.backtest import run_backtest


def make_rejection_fixture():
    rows = []
    index = pd.date_range("2026-01-08 09:35:00", periods=90, freq="min")
    price = 100.0

    for i, ts in enumerate(index):
        if i < 55:
            open_price = price
            close = price + (0.04 if i % 2 == 0 else -0.02)
            high = max(open_price, close) + 0.15
            low = min(open_price, close) - 0.15
            volume = 100 + (i % 6)
            price = close
        elif i == 55:
            open_price = 98.4
            high = 100.9
            low = 96.7
            close = 100.6
            volume = 220
            price = close
        elif i == 56:
            open_price = 100.6
            high = 102.2
            low = 100.1
            close = 101.8
            volume = 210
            price = close
        else:
            open_price = price
            close = price + 0.18
            high = close + 0.25
            low = open_price - 0.1
            volume = 130
            price = close

        rows.append(
            {
                "timestamp": ts,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )

    return pd.DataFrame(rows).set_index("timestamp")


def test_strategy_generates_reversal_signals():
    data = make_rejection_fixture()
    signals = generate_signals(
        data,
        {
            "zone_lookback": 50,
            "volume_mult": 1.05,
            "wick_ratio": 0.6,
            "risk_reward": 1.5,
            "max_hold_bars": 10,
            "use_time_filter": True,
            "reversal_windows": "09:35-11:00",
        },
    )

    assert len(signals) == len(data)
    assert signals.index.equals(data.index)
    assert (signals == 1).any(), "expected at least one long reversal signal"


def test_strategy_runs_through_backtester():
    data = make_rejection_fixture()
    results = run_backtest(
        data,
        "riley_coleman_reversal",
        {
            "zone_lookback": 50,
            "volume_mult": 1.05,
            "wick_ratio": 0.6,
            "risk_reward": 1.5,
            "max_hold_bars": 10,
            "use_time_filter": True,
            "reversal_windows": "09:35-11:00",
        },
    )

    assert results["metrics"]["total_trades"] >= 1
    assert "Riley" in STRATEGY_INFO["name"]


if __name__ == "__main__":
    test_strategy_generates_reversal_signals()
    test_strategy_runs_through_backtester()
    print("Riley Coleman-inspired strategy tests passed")
