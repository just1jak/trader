import sys
from pathlib import Path

import pandas as pd


BACKEND = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND))

from api.strategies.riley_coleman_transcript_strict import generate_signals, STRATEGY_INFO
from utils.backtest import run_backtest


def make_break_retest_fixture(start="2026-01-08 09:30:00"):
    rows = []
    index = pd.date_range(start, periods=85, freq="min")
    price = 99.0

    for i, ts in enumerate(index):
        if i < 45:
            open_price = price
            close = price + 0.03
            high = close + 0.12
            low = open_price - 0.12
            volume = 100 + (i % 5)
            price = close
        elif i == 45:
            open_price = price
            close = 101.05
            high = 101.25
            low = open_price - 0.08
            volume = 180
            price = close
        elif i == 46:
            open_price = 100.48
            close = 100.72
            high = 100.82
            low = 100.42
            volume = 170
            price = close
        elif i < 62:
            open_price = price
            close = price + 0.22
            high = close + 0.18
            low = open_price - 0.08
            volume = 135
            price = close
        else:
            open_price = price
            close = price + (0.02 if i % 2 == 0 else -0.01)
            high = max(open_price, close) + 0.1
            low = min(open_price, close) - 0.1
            volume = 110
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


def strict_params():
    return {
        "session_windows": "09:35-11:15",
        "zone_lookback": 30,
        "atr_period": 10,
        "volume_period": 15,
        "volume_mult": 1.05,
        "confirmation_volume_mult": 1.0,
        "ema_fast": 6,
        "ema_slow": 14,
        "min_trend_atr_mult": 0.02,
        "chop_range_atr_mult": 1.6,
        "breakout_atr_mult": 0.08,
        "retest_atr_mult": 0.45,
        "min_body_atr_mult": 0.12,
        "retest_expiry_bars": 5,
        "risk_reward": 1.4,
        "stop_atr_mult": 0.8,
        "max_hold_bars": 10,
        "allow_failed_breakout": False,
    }


def test_strict_strategy_generates_break_retest_signal():
    data = make_break_retest_fixture()
    signals = generate_signals(data, strict_params())

    assert len(signals) == len(data)
    assert signals.index.equals(data.index)
    assert (signals == 1).any(), "expected a long signal after breakout retest confirmation"
    assert not (signals == -1).any(), "fixture should not generate short signals"
    assert signals[signals == 1].index.min() >= pd.Timestamp("2026-01-08 10:16:00")


def test_strict_strategy_requires_configured_session_window():
    data = make_break_retest_fixture(start="2026-01-08 12:30:00")
    signals = generate_signals(data, strict_params())

    assert not (signals != 0).any(), "strict strategy should reject setups outside the morning window"


def test_strict_strategy_runs_through_backtester():
    data = make_break_retest_fixture()
    results = run_backtest(data, "riley_coleman_transcript_strict", strict_params())

    assert results["metrics"]["total_trades"] >= 1
    assert "Transcript Strict" in STRATEGY_INFO["name"]


if __name__ == "__main__":
    test_strict_strategy_generates_break_retest_signal()
    test_strict_strategy_requires_configured_session_window()
    test_strict_strategy_runs_through_backtester()
    print("Riley Coleman transcript-strict strategy tests passed")
