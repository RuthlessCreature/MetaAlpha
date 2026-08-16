import numpy as np
import pandas as pd

from metaalpha.market_baseline import (
    BASE_CONTINUOUS,
    TARGET_DIRECTION,
    add_market_baseline_features,
)


def _frame(n=80):
    dates = pd.bdate_range("2025-01-02", periods=n)
    close = 100.0 + np.arange(n) * 0.2 + np.sin(np.arange(n) / 5.0)
    open_ = close * (1.0 + 0.001 * np.cos(np.arange(n) / 4.0))
    high = np.maximum(open_, close) * 1.005
    low = np.minimum(open_, close) * 0.995
    volume = 1_000_000 + np.arange(n) * 5000
    return pd.DataFrame({"date": dates, "open": open_, "high": high, "low": low, "close": close, "volume": volume})


def test_market_predictors_do_not_use_same_session_ohlcv():
    raw = _frame()
    base = add_market_baseline_features(raw)
    row = 50

    changed = raw.copy()
    changed.loc[row, "open"] *= 1.10
    changed.loc[row, "high"] *= 1.12
    changed.loc[row, "low"] *= 0.90
    changed.loc[row, "close"] *= 1.08
    changed.loc[row, "volume"] *= 3.0
    altered = add_market_baseline_features(changed)

    # Current-session target is allowed to change; every registered predictor is not.
    assert altered.loc[row, TARGET_DIRECTION] != base.loc[row, TARGET_DIRECTION] or altered.loc[row, "same_session_return"] != base.loc[row, "same_session_return"]
    for col in BASE_CONTINUOUS:
        assert np.isclose(altered.loc[row, col], base.loc[row, col], equal_nan=True), col


def test_lagged_return_definition_is_previous_closes_only():
    raw = _frame()
    out = add_market_baseline_features(raw)
    row = 40
    expected_5 = raw.loc[row - 1, "close"] / raw.loc[row - 6, "close"] - 1.0
    assert np.isclose(out.loc[row, "ret_lag_5"], expected_5)
    expected_gap = raw.loc[row - 1, "open"] / raw.loc[row - 2, "close"] - 1.0
    assert np.isclose(out.loc[row, "overnight_gap_lag_1"], expected_gap)
