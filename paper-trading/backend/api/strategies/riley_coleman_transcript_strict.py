import pandas as pd
import numpy as np


def _truthy(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _parse_time_windows(windows):
    parsed = []
    if not windows:
        return parsed
    raw_windows = [part.strip() for part in windows.split(",")] if isinstance(windows, str) else windows

    for raw in raw_windows:
        if not raw:
            continue
        try:
            start, end = [part.strip() for part in raw.split("-", 1)]
            parsed.append((pd.to_datetime(start).time(), pd.to_datetime(end).time()))
        except (TypeError, ValueError):
            continue
    return parsed


def _in_time_windows(index, windows, require_intraday=True):
    if not isinstance(index, pd.DatetimeIndex) or not windows:
        return pd.Series(not require_intraday, index=index)

    times = pd.Series(index.time, index=index)
    if times.nunique() <= 1:
        return pd.Series(not require_intraday, index=index)

    allowed = pd.Series(False, index=index)
    for start, end in windows:
        if start <= end:
            allowed |= (times >= start) & (times <= end)
        else:
            allowed |= (times >= start) | (times <= end)
    return allowed


def _true_range(data):
    prev_close = data["close"].shift(1)
    ranges = pd.concat(
        [
            data["high"] - data["low"],
            (data["high"] - prev_close).abs(),
            (data["low"] - prev_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def generate_signals(data: pd.DataFrame, params: dict):
    """
    Transcript-strict Riley Coleman scalp model.

    This strategy only trades when the high-coverage transcript themes line up:
    morning/open timing, market-structure bias, a prior key level, a breakout or
    failed-break event, confirmation on retest, chop avoidance, and fixed
    risk/reward management.
    """
    params = params or {}
    required = {"open", "high", "low", "close"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns for strict Riley strategy: {sorted(missing)}")

    df = data.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "volume" not in df.columns:
        df["volume"] = 1.0

    zone_lookback = max(int(params.get("zone_lookback", 45)), 5)
    atr_period = max(int(params.get("atr_period", 14)), 2)
    volume_period = max(int(params.get("volume_period", 20)), 2)
    ema_fast_period = max(int(params.get("ema_fast", 9)), 2)
    ema_slow_period = max(int(params.get("ema_slow", 21)), ema_fast_period + 1)
    ema_slope_bars = max(int(params.get("ema_slope_bars", 3)), 1)
    chop_lookback = max(int(params.get("chop_lookback", 20)), 3)
    retest_expiry_bars = max(int(params.get("retest_expiry_bars", 8)), 1)
    max_hold_bars = max(int(params.get("max_hold_bars", 14)), 1)

    atr = _true_range(df).rolling(atr_period, min_periods=1).mean().shift(1)
    atr = atr.fillna((df["high"] - df["low"]).rolling(atr_period, min_periods=1).mean())
    atr = atr.replace(0, np.nan).ffill().fillna(1.0)

    resistance = df["high"].rolling(zone_lookback, min_periods=5).max().shift(1)
    support = df["low"].rolling(zone_lookback, min_periods=5).min().shift(1)

    volume_ma = df["volume"].rolling(volume_period, min_periods=1).mean().shift(1).fillna(df["volume"])
    volume_mult = float(params.get("volume_mult", 1.1))
    confirmation_volume_mult = float(params.get("confirmation_volume_mult", 1.0))
    volume_breakout_ok = df["volume"] >= volume_ma * volume_mult
    volume_confirm_ok = df["volume"] >= volume_ma * confirmation_volume_mult

    ema_fast = df["close"].ewm(span=ema_fast_period, adjust=False).mean()
    ema_slow = df["close"].ewm(span=ema_slow_period, adjust=False).mean()
    ema_slope = ema_fast - ema_fast.shift(ema_slope_bars)
    ema_gap = (ema_fast - ema_slow).abs()
    min_trend_atr_mult = float(params.get("min_trend_atr_mult", 0.08))
    trend_strength = ema_gap >= atr * min_trend_atr_mult
    long_bias = (ema_fast > ema_slow) & (ema_slope > 0) & (df["close"] > ema_slow) & trend_strength
    short_bias = (ema_fast < ema_slow) & (ema_slope < 0) & (df["close"] < ema_slow) & trend_strength

    rolling_range = (
        df["high"].rolling(chop_lookback, min_periods=3).max()
        - df["low"].rolling(chop_lookback, min_periods=3).min()
    ).shift(1)
    chop_range_atr_mult = float(params.get("chop_range_atr_mult", 2.2))
    not_choppy = rolling_range.fillna(0) >= atr * chop_range_atr_mult

    windows = _parse_time_windows(params.get("session_windows", "09:35-11:15"))
    time_ok = _in_time_windows(
        df.index,
        windows,
        require_intraday=_truthy(params.get("require_intraday_time"), default=True),
    )

    body = (df["close"] - df["open"]).abs()
    body_direction = df["close"] - df["open"]
    min_body_atr_mult = float(params.get("min_body_atr_mult", 0.18))
    impulse_body = body >= atr * min_body_atr_mult

    breakout_buffer = atr * float(params.get("breakout_atr_mult", 0.12))
    retest_tolerance = params.get("retest_tolerance")
    if retest_tolerance is None or float(retest_tolerance) <= 0:
        retest_tolerance = atr * float(params.get("retest_atr_mult", 0.32))
    else:
        retest_tolerance = pd.Series(float(retest_tolerance), index=df.index)

    breakout_up = (
        resistance.notna()
        & (df["close"] > resistance + breakout_buffer)
        & (body_direction > 0)
        & impulse_body
        & volume_breakout_ok
        & long_bias
        & not_choppy
        & time_ok
    )
    breakout_down = (
        support.notna()
        & (df["close"] < support - breakout_buffer)
        & (body_direction < 0)
        & impulse_body
        & volume_breakout_ok
        & short_bias
        & not_choppy
        & time_ok
    )

    candle_mid = (df["high"] + df["low"]) / 2
    bullish_confirm = (df["close"] > df["open"]) & (df["close"] > candle_mid) & volume_confirm_ok
    bearish_confirm = (df["close"] < df["open"]) & (df["close"] < candle_mid) & volume_confirm_ok

    allow_failed_breakout = _truthy(params.get("allow_failed_breakout"), default=True)
    failed_down_long = (
        allow_failed_breakout
        & support.notna()
        & (df["low"] < support - breakout_buffer)
        & (df["close"] > support)
        & bullish_confirm
        & long_bias
        & not_choppy
        & time_ok
    )
    failed_up_short = (
        allow_failed_breakout
        & resistance.notna()
        & (df["high"] > resistance + breakout_buffer)
        & (df["close"] < resistance)
        & bearish_confirm
        & short_bias
        & not_choppy
        & time_ok
    )

    risk_reward = float(params.get("risk_reward", 2.0))
    stop_atr_mult = float(params.get("stop_atr_mult", 0.9))

    signals = pd.Series(0, index=df.index)
    position = 0
    entry_price = None
    stop_price = None
    target_price = None
    bars_in_position = 0
    pending_direction = 0
    pending_level = None
    pending_age = 0

    for i, idx in enumerate(df.index):
        close = df["close"].iloc[i]
        high = df["high"].iloc[i]
        low = df["low"].iloc[i]
        current_atr = atr.iloc[i]
        tolerance = retest_tolerance.iloc[i]

        if position != 0:
            bars_in_position += 1
            hit_stop = low <= stop_price if position == 1 else high >= stop_price
            hit_target = high >= target_price if position == 1 else low <= target_price
            lost_bias = close < ema_slow.iloc[i] if position == 1 else close > ema_slow.iloc[i]
            if hit_stop or hit_target or lost_bias or bars_in_position >= max_hold_bars:
                position = 0
                entry_price = None
                stop_price = None
                target_price = None
                bars_in_position = 0

        if position == 0:
            entry_direction = 0
            entry_level = None

            if pending_direction == 1 and pending_level is not None:
                retested = low <= pending_level + tolerance and close >= pending_level
                if retested and bullish_confirm.iloc[i] and long_bias.iloc[i] and not_choppy.iloc[i] and time_ok.iloc[i]:
                    entry_direction = 1
                    entry_level = pending_level
            elif pending_direction == -1 and pending_level is not None:
                retested = high >= pending_level - tolerance and close <= pending_level
                if retested and bearish_confirm.iloc[i] and short_bias.iloc[i] and not_choppy.iloc[i] and time_ok.iloc[i]:
                    entry_direction = -1
                    entry_level = pending_level

            if entry_direction == 0 and failed_down_long.iloc[i]:
                entry_direction = 1
                entry_level = support.iloc[i]
            elif entry_direction == 0 and failed_up_short.iloc[i]:
                entry_direction = -1
                entry_level = resistance.iloc[i]

            if entry_direction != 0 and entry_level is not None:
                position = entry_direction
                entry_price = close
                structure_risk = abs(entry_price - entry_level) + tolerance
                risk = max(current_atr * stop_atr_mult, structure_risk, tolerance)
                if position == 1:
                    stop_price = entry_price - risk
                    target_price = entry_price + risk * risk_reward
                else:
                    stop_price = entry_price + risk
                    target_price = entry_price - risk * risk_reward
                bars_in_position = 0
                pending_direction = 0
                pending_level = None
                pending_age = 0

        if position == 0:
            if breakout_up.iloc[i]:
                pending_direction = 1
                pending_level = resistance.iloc[i]
                pending_age = 0
            elif breakout_down.iloc[i]:
                pending_direction = -1
                pending_level = support.iloc[i]
                pending_age = 0
            elif pending_direction != 0:
                pending_age += 1
                if pending_age > retest_expiry_bars:
                    pending_direction = 0
                    pending_level = None
                    pending_age = 0

        signals.iloc[i] = position

    return signals


STRATEGY_INFO = {
    "name": "Riley Coleman Transcript Strict Morning Scalp",
    "description": (
        "Strict mechanical strategy distilled from 80 public Riley Coleman transcripts: "
        "morning timing, trend/structure bias, key-level breakout or failed-break setup, "
        "confirmation on retest, chop avoidance, and fixed risk/reward exits."
    ),
    "source_artifacts": {
        "strategy_spec": "paper-trading/data/strategy-research/riley_coleman/strategy_spec.json",
        "evidence": "paper-trading/data/strategy-research/riley_coleman/evidence.jsonl",
    },
    "parameters": {
        "session_windows": {"default": "09:35-11:15", "description": "Comma-separated entry windows"},
        "zone_lookback": {"default": 45, "description": "Bars used to define prior support/resistance"},
        "atr_period": {"default": 14, "description": "ATR period for buffers, tolerance, and stops"},
        "volume_mult": {"default": 1.1, "description": "Breakout volume multiplier"},
        "confirmation_volume_mult": {"default": 1.0, "description": "Retest confirmation volume multiplier"},
        "ema_fast": {"default": 9, "description": "Fast EMA for trend/structure bias"},
        "ema_slow": {"default": 21, "description": "Slow EMA for trend/structure bias"},
        "min_trend_atr_mult": {"default": 0.08, "description": "Minimum EMA separation as ATR multiple"},
        "chop_range_atr_mult": {"default": 2.2, "description": "Minimum prior range as ATR multiple"},
        "breakout_atr_mult": {"default": 0.12, "description": "Level break buffer as ATR multiple"},
        "retest_atr_mult": {"default": 0.32, "description": "Retest tolerance as ATR multiple"},
        "min_body_atr_mult": {"default": 0.18, "description": "Minimum breakout candle body as ATR multiple"},
        "retest_expiry_bars": {"default": 8, "description": "Bars allowed between break and retest"},
        "risk_reward": {"default": 2.0, "description": "Target distance as a multiple of initial risk"},
        "stop_atr_mult": {"default": 0.9, "description": "Minimum stop distance as ATR multiple"},
        "max_hold_bars": {"default": 14, "description": "Maximum bars to hold a scalp"},
        "allow_failed_breakout": {"default": True, "description": "Allow failed breakout/trap reversal entries"},
        "require_intraday_time": {"default": True, "description": "Disable entries when intraday timestamps are absent"},
    },
}
