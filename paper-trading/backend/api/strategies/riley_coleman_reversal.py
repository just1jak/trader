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
    if isinstance(windows, str):
        raw_windows = [part.strip() for part in windows.split(",")]
    else:
        raw_windows = windows

    for raw in raw_windows:
        if not raw:
            continue
        try:
            start, end = [part.strip() for part in raw.split("-", 1)]
            parsed.append((pd.to_datetime(start).time(), pd.to_datetime(end).time()))
        except (TypeError, ValueError):
            continue
    return parsed


def _in_time_windows(index, windows):
    if not isinstance(index, pd.DatetimeIndex) or not windows:
        return pd.Series(True, index=index)

    times = pd.Series(index.time, index=index)
    # Daily bars often arrive at midnight; do not accidentally filter all of them out.
    if times.nunique() <= 1:
        return pd.Series(True, index=index)

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
    Riley Coleman-inspired reversal/scalping strategy.

    This translates the recurring public-video themes into mechanical rules:
    define key support/resistance zones, wait for a rejection or break-and-retest,
    optionally restrict entries to common intraday reversal windows, and manage
    exits with ATR-based stops, risk/reward targets, and max hold time.
    """
    params = params or {}
    required = {"open", "high", "low", "close"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns for Riley strategy: {sorted(missing)}")

    df = data.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "volume" not in df.columns:
        df["volume"] = 1.0

    zone_lookback = int(params.get("zone_lookback", 50))
    atr_period = int(params.get("atr_period", 14))
    volume_period = int(params.get("volume_period", 20))
    max_hold_bars = int(params.get("max_hold_bars", 20))
    retest_expiry_bars = int(params.get("retest_expiry_bars", 8))

    zone_lookback = max(zone_lookback, 3)
    atr_period = max(atr_period, 2)
    volume_period = max(volume_period, 2)
    max_hold_bars = max(max_hold_bars, 1)
    retest_expiry_bars = max(retest_expiry_bars, 1)

    atr = _true_range(df).rolling(atr_period, min_periods=1).mean().shift(1)
    atr = atr.fillna((df["high"] - df["low"]).rolling(atr_period, min_periods=1).mean())
    atr = atr.replace(0, np.nan).ffill().fillna(1.0)

    tolerance = params.get("retest_tolerance")
    if tolerance is None or float(tolerance) <= 0:
        tolerance = atr * float(params.get("atr_tolerance_mult", 0.35))
    else:
        tolerance = pd.Series(float(tolerance), index=df.index)

    support = df["low"].rolling(zone_lookback, min_periods=3).min().shift(1)
    resistance = df["high"].rolling(zone_lookback, min_periods=3).max().shift(1)
    volume_ma = df["volume"].rolling(volume_period, min_periods=1).mean().shift(1)
    volume_ok = df["volume"] >= volume_ma.fillna(df["volume"]) * float(params.get("volume_mult", 1.05))

    body = (df["close"] - df["open"]).abs()
    body_floor = atr * 0.05
    lower_wick = df[["open", "close"]].min(axis=1) - df["low"]
    upper_wick = df["high"] - df[["open", "close"]].max(axis=1)
    wick_ratio = float(params.get("wick_ratio", 1.2))
    bullish_rejection = (
        (df["close"] > df["open"])
        & (lower_wick >= (body + body_floor) * wick_ratio)
        & (df["close"] > df["close"].shift(1))
    )
    bearish_rejection = (
        (df["close"] < df["open"])
        & (upper_wick >= (body + body_floor) * wick_ratio)
        & (df["close"] < df["close"].shift(1))
    )

    trend_ema = int(params.get("trend_ema", 50))
    ema = df["close"].ewm(span=max(trend_ema, 2), adjust=False).mean()
    trend_filter = _truthy(params.get("trend_filter"), default=False)
    long_bias = (df["close"] >= ema) | (~trend_filter)
    short_bias = (df["close"] <= ema) | (~trend_filter)

    windows = _parse_time_windows(params.get("reversal_windows", "09:35-11:00,13:30-15:45"))
    use_time_filter = _truthy(params.get("use_time_filter"), default=True)
    time_ok = _in_time_windows(df.index, windows) if use_time_filter else pd.Series(True, index=df.index)

    near_support = support.notna() & (df["low"] <= support + tolerance) & (df["close"] >= support)
    near_resistance = resistance.notna() & (df["high"] >= resistance - tolerance) & (df["close"] <= resistance)
    demand_reversal = near_support & bullish_rejection & volume_ok & long_bias & time_ok
    supply_reversal = near_resistance & bearish_rejection & volume_ok & short_bias & time_ok

    breakout_up = resistance.notna() & (df["close"] > resistance + tolerance) & volume_ok & long_bias & time_ok
    breakout_down = support.notna() & (df["close"] < support - tolerance) & volume_ok & short_bias & time_ok

    risk_reward = float(params.get("risk_reward", 1.75))
    stop_atr_mult = float(params.get("stop_atr_mult", 1.0))
    enable_break_retest = _truthy(params.get("enable_break_retest"), default=True)

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

        if position != 0:
            bars_in_position += 1
            hit_stop = low <= stop_price if position == 1 else high >= stop_price
            hit_target = high >= target_price if position == 1 else low <= target_price
            opposite_setup = supply_reversal.iloc[i] if position == 1 else demand_reversal.iloc[i]
            if hit_stop or hit_target or opposite_setup or bars_in_position >= max_hold_bars:
                position = 0
                entry_price = None
                stop_price = None
                target_price = None
                bars_in_position = 0

        if position == 0:
            entry_direction = 0
            if demand_reversal.iloc[i]:
                entry_direction = 1
            elif supply_reversal.iloc[i]:
                entry_direction = -1
            elif enable_break_retest and pending_direction != 0 and pending_level is not None:
                if pending_direction == 1:
                    retest = low <= pending_level + tolerance.iloc[i] and close >= pending_level
                    if retest and bullish_rejection.iloc[i] and volume_ok.iloc[i]:
                        entry_direction = 1
                else:
                    retest = high >= pending_level - tolerance.iloc[i] and close <= pending_level
                    if retest and bearish_rejection.iloc[i] and volume_ok.iloc[i]:
                        entry_direction = -1

            if entry_direction != 0:
                position = entry_direction
                entry_price = close
                risk = max(current_atr * stop_atr_mult, tolerance.iloc[i])
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

        if position == 0 and enable_break_retest:
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
    "name": "Riley Coleman-Inspired Reversal Scalp",
    "description": (
        "Mechanical futures scalping model derived from public Riley Coleman video "
        "themes: key zones, rejection candles, reversal timing windows, break/retest, "
        "and fixed risk/reward management."
    ),
    "parameters": {
        "zone_lookback": {"default": 50, "description": "Bars used to identify support/resistance zones"},
        "atr_period": {"default": 14, "description": "ATR period for dynamic tolerance and stops"},
        "atr_tolerance_mult": {"default": 0.35, "description": "Zone tolerance as ATR multiple when retest_tolerance is 0"},
        "retest_tolerance": {"default": 0, "description": "Fixed price-unit zone tolerance; 0 uses ATR tolerance"},
        "volume_mult": {"default": 1.05, "description": "Volume confirmation multiplier versus recent average"},
        "wick_ratio": {"default": 1.2, "description": "Minimum rejection-wick size relative to candle body"},
        "risk_reward": {"default": 1.75, "description": "Target distance as a multiple of initial risk"},
        "stop_atr_mult": {"default": 1.0, "description": "Initial stop distance as ATR multiple"},
        "max_hold_bars": {"default": 20, "description": "Maximum bars to hold a scalp"},
        "use_time_filter": {"default": True, "description": "Restrict entries to reversal windows"},
        "reversal_windows": {"default": "09:35-11:00,13:30-15:45", "description": "Comma-separated intraday windows"},
        "enable_break_retest": {"default": True, "description": "Allow breakout then retest entries"},
        "trend_filter": {"default": False, "description": "Require long above / short below trend EMA"},
        "trend_ema": {"default": 50, "description": "EMA period for optional trend filter"},
    },
}
