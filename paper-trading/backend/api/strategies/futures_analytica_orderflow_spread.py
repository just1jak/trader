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


def _numeric_series(data, column, default=0.0):
    if column in data.columns:
        return pd.to_numeric(data[column], errors="coerce").fillna(default)
    return pd.Series(default, index=data.index, dtype="float64")


def _depth_sum(data, side, levels):
    direct_name = f"{side}_depth"
    if direct_name in data.columns:
        return _numeric_series(data, direct_name)

    columns = [
        f"{side}_size_{level}"
        for level in range(1, levels + 1)
        if f"{side}_size_{level}" in data.columns
    ]
    if columns:
        depth = pd.Series(0.0, index=data.index)
        for column in columns:
            depth = depth + _numeric_series(data, column)
        return depth

    if side == "bid":
        direction = np.where(data["close"] >= data["open"], 1.0, 0.35)
    else:
        direction = np.where(data["close"] < data["open"], 1.0, 0.35)
    return pd.Series(direction, index=data.index) * _numeric_series(data, "volume", default=1.0)


def _order_side_from_data(data, mid):
    if "order_side" in data.columns:
        raw = data["order_side"].astype(str).str.lower()
        side = pd.Series(0, index=data.index, dtype="int64")
        side[raw.isin(["buy", "bid", "long", "1"])] = 1
        side[raw.isin(["sell", "ask", "short", "-1"])] = -1
        return side

    if "order_price" in data.columns:
        order_price = _numeric_series(data, "order_price")
        side = pd.Series(0, index=data.index, dtype="int64")
        side[order_price > mid] = 1
        side[order_price < mid] = -1
        return side

    return pd.Series(0, index=data.index, dtype="int64")


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
    Futures Analytica-inspired order-flow/spread strategy.

    This mechanical version combines L2Azimuth/DEX/Trespass-style ideas:
    bid/ask depth imbalance, large aggressive orders inside the spread,
    spoofing/microprobability gates when columns are available, and footprint
    confirmation from delta, saturation, or unfinished auction proxies.
    """
    params = params or {}
    required = {"open", "high", "low", "close"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns for Futures Analytica strategy: {sorted(missing)}")

    df = data.copy()
    if "volume" not in df.columns:
        df["volume"] = 1.0
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").ffill().fillna(0)

    depth_levels = max(int(params.get("depth_levels", 5)), 1)
    imbalance_threshold = float(params.get("imbalance_threshold", 0.5))
    microprob_threshold = float(params.get("microprob_threshold", 0.8))
    spoofing_max = float(params.get("spoofing_max", 0.4))
    spread_max_ticks = float(params.get("spread_max_ticks", 4.0))
    tick_size = float(params.get("tick_size", 0.25))
    large_order_mult = float(params.get("large_order_mult", 2.0))
    saturation_z = float(params.get("saturation_z", 1.2))
    delta_threshold = float(params.get("delta_threshold", 0.35))
    atr_period = max(int(params.get("atr_period", 14)), 2)
    risk_reward = float(params.get("risk_reward", 1.5))
    stop_atr_mult = float(params.get("stop_atr_mult", 0.8))
    max_hold_bars = max(int(params.get("max_hold_bars", 12)), 1)
    require_in_spread_order = _truthy(params.get("require_in_spread_order"), default=False)
    allow_ohlcv_proxy = _truthy(params.get("allow_ohlcv_proxy"), default=True)

    bid_depth = _depth_sum(df, "bid", depth_levels)
    ask_depth = _depth_sum(df, "ask", depth_levels)
    total_depth = (bid_depth + ask_depth).replace(0, np.nan)
    book_imbalance = ((bid_depth - ask_depth) / total_depth).replace([np.inf, -np.inf], np.nan).fillna(0)

    if "delta" in df.columns:
        delta = _numeric_series(df, "delta")
    else:
        delta = (df["close"] - df["open"]) * df["volume"]
    delta_norm = (
        delta.rolling(3, min_periods=1).mean()
        / df["volume"].rolling(3, min_periods=1).mean().replace(0, np.nan)
    ).replace([np.inf, -np.inf], np.nan).fillna(0)

    if {"best_bid", "best_ask"}.issubset(df.columns):
        best_bid = _numeric_series(df, "best_bid")
        best_ask = _numeric_series(df, "best_ask")
        spread = (best_ask - best_bid).clip(lower=0)
        mid = (best_bid + best_ask) / 2
    else:
        spread = _numeric_series(df, "spread", default=tick_size)
        spread = spread.where(spread > 0, tick_size)
        mid = df[["open", "close"]].mean(axis=1)
        best_bid = mid - spread / 2
        best_ask = mid + spread / 2

    spread_ticks = spread / max(tick_size, 1e-9)
    spread_ok = spread_ticks <= spread_max_ticks

    order_size = _numeric_series(df, "order_size", default=0)
    order_size_ma = order_size.rolling(30, min_periods=1).mean().replace(0, np.nan)
    large_order = order_size > order_size_ma.fillna(order_size) * large_order_mult
    if "order_price" in df.columns:
        order_price = _numeric_series(df, "order_price")
        in_spread = (order_price > best_bid) & (order_price < best_ask)
    else:
        in_spread = pd.Series(False, index=df.index)
    order_side = _order_side_from_data(df, mid)
    in_spread_aggression = in_spread & large_order & (order_side != 0)

    spoofing_score = _numeric_series(df, "spoofing_score", default=0.0)
    spoofing_ok = spoofing_score <= spoofing_max
    microprob = _numeric_series(df, "microprobability", default=np.nan)
    microprob_dir = _numeric_series(df, "microprobability_direction", default=0)
    hf_omega = _numeric_series(df, "hf_omega", default=1.0)

    long_forecast = (microprob.isna()) | ((microprob >= microprob_threshold) & (microprob_dir >= 0))
    short_forecast = (microprob.isna()) | ((microprob >= microprob_threshold) & (microprob_dir <= 0))
    omega_ok = hf_omega > 0

    volume_ma = df["volume"].rolling(30, min_periods=1).mean()
    volume_std = df["volume"].rolling(30, min_periods=2).std().replace(0, np.nan)
    volume_z = ((df["volume"] - volume_ma) / volume_std).replace([np.inf, -np.inf], np.nan).fillna(0)
    candle_range = (df["high"] - df["low"]).replace(0, np.nan)
    close_location = ((df["close"] - df["low"]) / candle_range).clip(0, 1).fillna(0.5)
    body_ratio = ((df["close"] - df["open"]).abs() / candle_range).replace([np.inf, -np.inf], np.nan).fillna(0)

    unusual_saturation = volume_z >= saturation_z
    unfinished_buy = close_location >= 0.78
    unfinished_sell = close_location <= 0.22
    absorption = unusual_saturation & (body_ratio <= 0.55)

    long_pressure = (
        (book_imbalance >= imbalance_threshold)
        | (delta_norm >= delta_threshold)
        | ((order_side == 1) & in_spread_aggression)
    )
    short_pressure = (
        (book_imbalance <= -imbalance_threshold)
        | (delta_norm <= -delta_threshold)
        | ((order_side == -1) & in_spread_aggression)
    )

    if require_in_spread_order:
        long_pressure &= (order_side == 1) & in_spread_aggression
        short_pressure &= (order_side == -1) & in_spread_aggression
    elif not allow_ohlcv_proxy and not any(
        col in df.columns
        for col in ["bid_depth", "ask_depth", "bid_size_1", "ask_size_1", "delta", "order_price"]
    ):
        long_pressure &= False
        short_pressure &= False

    long_confirm = absorption | unfinished_buy | (in_spread_aggression & (order_side == 1))
    short_confirm = absorption | unfinished_sell | (in_spread_aggression & (order_side == -1))

    long_setup = long_pressure & long_confirm & spread_ok & spoofing_ok & long_forecast & omega_ok
    short_setup = short_pressure & short_confirm & spread_ok & spoofing_ok & short_forecast & omega_ok

    atr = _true_range(df).rolling(atr_period, min_periods=1).mean().replace(0, np.nan).ffill().fillna(tick_size)
    signals = pd.Series(0, index=df.index)
    position = 0
    entry_price = None
    stop_price = None
    target_price = None
    bars_in_position = 0

    for i, idx in enumerate(df.index):
        close = df["close"].iloc[i]
        high = df["high"].iloc[i]
        low = df["low"].iloc[i]

        if position != 0:
            bars_in_position += 1
            hit_stop = low <= stop_price if position == 1 else high >= stop_price
            hit_target = high >= target_price if position == 1 else low <= target_price
            opposite = short_setup.iloc[i] if position == 1 else long_setup.iloc[i]
            book_faded = book_imbalance.iloc[i] < 0 if position == 1 else book_imbalance.iloc[i] > 0
            if hit_stop or hit_target or opposite or book_faded or bars_in_position >= max_hold_bars:
                position = 0
                entry_price = None
                stop_price = None
                target_price = None
                bars_in_position = 0

        if position == 0:
            if long_setup.iloc[i] and not short_setup.iloc[i]:
                position = 1
            elif short_setup.iloc[i] and not long_setup.iloc[i]:
                position = -1

            if position != 0:
                entry_price = close
                risk = max(atr.iloc[i] * stop_atr_mult, tick_size)
                if position == 1:
                    stop_price = entry_price - risk
                    target_price = entry_price + risk * risk_reward
                else:
                    stop_price = entry_price + risk
                    target_price = entry_price - risk * risk_reward
                bars_in_position = 0

        signals.iloc[i] = position

    return signals


STRATEGY_INFO = {
    "name": "Futures Analytica-Inspired Order Flow Spread",
    "description": (
        "Mechanical L2/footprint strategy inspired by Futures Analytica themes: "
        "bid/ask depth imbalance, in-spread aggressive orders, delta/volume "
        "saturation, spoofing filters, and short hold-time execution."
    ),
    "parameters": {
        "depth_levels": {"default": 5, "description": "Number of bid_size_N/ask_size_N levels to aggregate"},
        "imbalance_threshold": {"default": 0.5, "description": "Minimum normalized bid/ask imbalance"},
        "microprob_threshold": {"default": 0.8, "description": "Optional microprobability gate when provided"},
        "spoofing_max": {"default": 0.4, "description": "Maximum allowed spoofing_score when provided"},
        "spread_max_ticks": {"default": 4.0, "description": "Maximum best bid/ask spread in ticks"},
        "tick_size": {"default": 0.25, "description": "Instrument tick size"},
        "large_order_mult": {"default": 2.0, "description": "In-spread order size multiple versus recent average"},
        "saturation_z": {"default": 1.2, "description": "Volume z-score threshold for unusual saturation"},
        "delta_threshold": {"default": 0.35, "description": "Normalized delta confirmation threshold"},
        "atr_period": {"default": 14, "description": "ATR period for stops and targets"},
        "risk_reward": {"default": 1.5, "description": "Target distance as a multiple of initial risk"},
        "stop_atr_mult": {"default": 0.8, "description": "Stop distance as ATR multiple"},
        "max_hold_bars": {"default": 12, "description": "Maximum bars to hold a position"},
        "require_in_spread_order": {"default": False, "description": "Require a large order inside bid/ask spread"},
        "allow_ohlcv_proxy": {"default": True, "description": "Fallback to OHLCV/delta proxies when L2 columns are missing"},
    },
}
