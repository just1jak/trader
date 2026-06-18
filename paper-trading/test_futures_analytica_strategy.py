import sys
from pathlib import Path

import pandas as pd


BACKEND = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND))

from api.strategies.futures_analytica_orderflow_spread import generate_signals, STRATEGY_INFO
from utils.backtest import run_backtest


def make_orderflow_fixture():
    rows = []
    index = pd.date_range("2026-01-08 09:30:00", periods=80, freq="min")
    price = 100.0

    for i, ts in enumerate(index):
        open_price = price
        close = price + 0.02
        high = close + 0.1
        low = open_price - 0.1
        volume = 100
        best_bid = close - 0.125
        best_ask = close + 0.125
        bid_size = 100
        ask_size = 100
        order_price = close
        order_size = 0
        order_side = ""
        delta = 0
        microprobability = 0.5
        microprobability_direction = 0
        spoofing_score = 0.1
        hf_omega = 1.0

        if i == 45:
            close = price + 0.7
            high = close + 0.18
            low = open_price - 0.08
            volume = 260
            best_bid = close - 0.125
            best_ask = close + 0.125
            bid_size = 480
            ask_size = 90
            order_price = best_ask - 0.05
            order_size = 650
            order_side = "buy"
            delta = 220
            microprobability = 0.86
            microprobability_direction = 1
        elif i > 45:
            close = price + 0.22
            high = close + 0.12
            low = open_price - 0.06
            volume = 140
            bid_size = 260
            ask_size = 120
            delta = 80
            microprobability = 0.82
            microprobability_direction = 1

        rows.append(
            {
                "timestamp": ts,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "best_bid": best_bid,
                "best_ask": best_ask,
                "bid_size_1": bid_size,
                "ask_size_1": ask_size,
                "order_price": order_price,
                "order_size": order_size,
                "order_side": order_side,
                "delta": delta,
                "microprobability": microprobability,
                "microprobability_direction": microprobability_direction,
                "spoofing_score": spoofing_score,
                "hf_omega": hf_omega,
            }
        )
        price = close

    return pd.DataFrame(rows).set_index("timestamp")


def params():
    return {
        "depth_levels": 1,
        "imbalance_threshold": 0.45,
        "microprob_threshold": 0.8,
        "spoofing_max": 0.4,
        "spread_max_ticks": 2,
        "tick_size": 0.25,
        "large_order_mult": 2,
        "saturation_z": 0.8,
        "delta_threshold": 0.3,
        "risk_reward": 1.2,
        "max_hold_bars": 8,
        "require_in_spread_order": True,
    }


def test_strategy_generates_in_spread_orderflow_signal():
    data = make_orderflow_fixture()
    signals = generate_signals(data, params())

    assert len(signals) == len(data)
    assert signals.index.equals(data.index)
    assert (signals == 1).any(), "expected a long signal from in-spread orderflow aggression"


def test_strategy_runs_through_backtester():
    results = run_backtest(data=make_orderflow_fixture(), strategy_name="futures_analytica_orderflow_spread", params=params())

    assert results["metrics"]["total_trades"] >= 1
    assert "Futures Analytica" in STRATEGY_INFO["name"]


if __name__ == "__main__":
    test_strategy_generates_in_spread_orderflow_signal()
    test_strategy_runs_through_backtester()
    print("Futures Analytica-inspired strategy tests passed")
