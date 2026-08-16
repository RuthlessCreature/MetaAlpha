import numpy as np
import pandas as pd

from metaalpha.market_baseline import (
    BASE_CATEGORICAL,
    BASE_CONTINUOUS,
    add_market_baseline_features,
    premarket_market_feature_row,
)
from metaalpha.research_hybrid_alpha import SYMBOLIC_BLOCKS
from metaalpha.symbolic_state import premarket_symbolic_feature_row
from metaalpha.pipeline import build_dataset
from metaalpha.calendar_cycle import add_calendar_cycle_features


def _frame(n=100):
    dates = pd.bdate_range("2025-01-02", periods=n)
    idx = np.arange(n, dtype=float)
    close = 100.0 + idx * 0.15 + np.sin(idx / 4.0)
    open_ = close * (1.0 + 0.002 * np.cos(idx / 7.0))
    high = np.maximum(open_, close) * 1.006
    low = np.minimum(open_, close) * 0.994
    volume = 1_000_000.0 + idx * 3500.0 + 10_000.0 * np.sin(idx / 9.0)
    return pd.DataFrame({"date": dates, "open": open_, "high": high, "low": low, "close": close, "volume": volume})


def test_premarket_market_row_equals_historical_batch_features():
    raw = _frame()
    target_index = 75
    target_date = raw.loc[target_index, "date"]
    batch = add_market_baseline_features(raw)
    premkt = premarket_market_feature_row(raw.iloc[:target_index].copy(), target_date)
    for col in BASE_CONTINUOUS + BASE_CATEGORICAL:
        a = batch.loc[target_index, col]
        b = premkt.loc[0, col]
        if col in BASE_CATEGORICAL:
            assert int(a) == int(b), col
        else:
            assert np.isclose(float(a), float(b), rtol=0.0, atol=1e-12), (col, a, b)


def test_premarket_symbolic_row_equals_historical_feature_stack():
    raw = _frame(30)
    target_index = 20
    target_date = raw.loc[target_index, "date"]
    batch = build_dataset(raw[["date", "close"]].copy(), include_ziping=True)
    batch = add_calendar_cycle_features(batch)
    premkt = premarket_symbolic_feature_row(target_date)

    cols = SYMBOLIC_BLOCKS["cycle"] + SYMBOLIC_BLOCKS["ziping"]
    for col in cols:
        assert str(batch.loc[target_index, col]) == str(premkt.loc[0, col]), col
