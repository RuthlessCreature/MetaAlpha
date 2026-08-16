from __future__ import annotations

import numpy as np
import pandas as pd


BASE_CONTINUOUS = [
    "ret_lag_1",
    "ret_lag_2",
    "ret_lag_5",
    "ret_lag_10",
    "ret_lag_20",
    "abs_ret_lag_1",
    "vol_lag_5",
    "vol_lag_20",
    "overnight_gap_lag_1",
    "intraday_range_lag_1",
    "close_ma5_distance_lag_1",
    "close_ma20_distance_lag_1",
    "drawdown_20_lag_1",
    "volume_log_change_lag_1",
    "volume_z20_lag_1",
    "normalized_time",
    "normalized_time_squared",
]

BASE_CATEGORICAL = ["weekday", "gregorian_month"]
TARGET_DIRECTION = "same_session_direction"
TARGET_RETURN = "same_session_return"

_EPOCH = pd.Timestamp("1990-12-19")
_TIME_SCALE_DAYS = 365.25 * 40.0


def _trailing_return(close: pd.Series, sessions: int) -> pd.Series:
    """Return known at 09:25 on t over the previous `sessions` closes.

    At row t this is close[t-1] / close[t-1-sessions] - 1.
    """
    return close.shift(1) / close.shift(sessions + 1) - 1.0


def _normalize_market_history(df: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"market baseline requires columns: {sorted(missing)}")
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.normalize()
    out = out.sort_values("date").reset_index(drop=True)
    for c in ("open", "high", "low", "close", "volume"):
        out[c] = pd.to_numeric(out[c], errors="raise")
    if (out[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("non-positive OHLC value")
    if (out["volume"] <= 0).any():
        raise ValueError("non-positive volume value")
    return out


def add_market_baseline_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the frozen HYBRID_ALPHA_001 market baseline without lookahead.

    All market predictors at row t use only OHLCV observations through t-1.
    The only row-t market values emitted are audit targets, never predictors.
    """
    out = _normalize_market_history(df)

    close = out["close"].astype(float)
    open_ = out["open"].astype(float)
    high = out["high"].astype(float)
    low = out["low"].astype(float)
    volume = out["volume"].astype(float)

    ret = close.pct_change()
    out[TARGET_RETURN] = ret
    direction = pd.Series(np.nan, index=out.index, dtype=float)
    direction.loc[ret.notna()] = (ret.loc[ret.notna()] > 0.0).astype(float)
    out[TARGET_DIRECTION] = direction

    for h in (1, 2, 5, 10, 20):
        out[f"ret_lag_{h}"] = _trailing_return(close, h)

    out["abs_ret_lag_1"] = ret.shift(1).abs()
    out["vol_lag_5"] = ret.shift(1).rolling(5, min_periods=5).std(ddof=1)
    out["vol_lag_20"] = ret.shift(1).rolling(20, min_periods=20).std(ddof=1)

    overnight_gap = open_ / close.shift(1) - 1.0
    out["overnight_gap_lag_1"] = overnight_gap.shift(1)

    intraday_range = (high - low) / close
    out["intraday_range_lag_1"] = intraday_range.shift(1)

    ma5 = close.rolling(5, min_periods=5).mean()
    ma20 = close.rolling(20, min_periods=20).mean()
    out["close_ma5_distance_lag_1"] = close.shift(1) / ma5.shift(1) - 1.0
    out["close_ma20_distance_lag_1"] = close.shift(1) / ma20.shift(1) - 1.0

    trailing_peak20 = close.rolling(20, min_periods=20).max()
    out["drawdown_20_lag_1"] = close.shift(1) / trailing_peak20.shift(1) - 1.0

    log_volume = np.log(volume)
    out["volume_log_change_lag_1"] = log_volume.diff().shift(1)
    volume_mean20 = log_volume.rolling(20, min_periods=20).mean()
    volume_std20 = log_volume.rolling(20, min_periods=20).std(ddof=1)
    z20 = (log_volume - volume_mean20) / volume_std20.replace(0.0, np.nan)
    out["volume_z20_lag_1"] = z20.shift(1)

    days = (out["date"] - _EPOCH).dt.days.astype(float)
    out["normalized_time"] = days / _TIME_SCALE_DAYS
    out["normalized_time_squared"] = out["normalized_time"] ** 2
    out["weekday"] = out["date"].dt.weekday.astype(int)
    out["gregorian_month"] = out["date"].dt.month.astype(int)

    return out


def premarket_market_feature_row(history: pd.DataFrame, target_date: str | pd.Timestamp) -> pd.DataFrame:
    """Construct the frozen 09:25 predictor row using only history through t-1.

    Unlike the historical batch builder, this function never accepts or invents
    current-session OHLCV. It is therefore the canonical forward-prediction path.
    """
    h = _normalize_market_history(history)
    target = pd.Timestamp(target_date).normalize()
    if h.empty:
        raise ValueError("empty market history")
    if h["date"].iloc[-1] >= target:
        raise ValueError("premarket history must end strictly before target_date")
    if len(h) < 22:
        raise ValueError("at least 22 prior market sessions are required")

    close = h["close"].astype(float)
    open_ = h["open"].astype(float)
    high = h["high"].astype(float)
    low = h["low"].astype(float)
    volume = h["volume"].astype(float)
    ret = close.pct_change()

    row: dict[str, object] = {"date": target}
    for sessions in (1, 2, 5, 10, 20):
        row[f"ret_lag_{sessions}"] = float(close.iloc[-1] / close.iloc[-1 - sessions] - 1.0)
    row["abs_ret_lag_1"] = float(abs(ret.iloc[-1]))
    row["vol_lag_5"] = float(ret.iloc[-5:].std(ddof=1))
    row["vol_lag_20"] = float(ret.iloc[-20:].std(ddof=1))
    row["overnight_gap_lag_1"] = float(open_.iloc[-1] / close.iloc[-2] - 1.0)
    row["intraday_range_lag_1"] = float((high.iloc[-1] - low.iloc[-1]) / close.iloc[-1])
    row["close_ma5_distance_lag_1"] = float(close.iloc[-1] / close.iloc[-5:].mean() - 1.0)
    row["close_ma20_distance_lag_1"] = float(close.iloc[-1] / close.iloc[-20:].mean() - 1.0)
    row["drawdown_20_lag_1"] = float(close.iloc[-1] / close.iloc[-20:].max() - 1.0)

    log_volume = np.log(volume)
    row["volume_log_change_lag_1"] = float(log_volume.iloc[-1] - log_volume.iloc[-2])
    last20 = log_volume.iloc[-20:]
    row["volume_z20_lag_1"] = float((last20.iloc[-1] - last20.mean()) / last20.std(ddof=1))

    normalized_time = float((target - _EPOCH).days / _TIME_SCALE_DAYS)
    row["normalized_time"] = normalized_time
    row["normalized_time_squared"] = normalized_time**2
    row["weekday"] = int(target.weekday())
    row["gregorian_month"] = int(target.month)
    return pd.DataFrame([row])


def eligible_hybrid_rows(df: pd.DataFrame, extra_features: list[str] | None = None) -> pd.Series:
    required = BASE_CONTINUOUS + BASE_CATEGORICAL + [TARGET_DIRECTION, TARGET_RETURN]
    if extra_features:
        required += list(extra_features)
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"hybrid frame missing columns: {missing}")
    return df[required].notna().all(axis=1)
