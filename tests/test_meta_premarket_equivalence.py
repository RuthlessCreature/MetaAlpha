import numpy as np
import pandas as pd

from metaalpha.meta_branch import (
    META_CANDIDATE_FEATURES,
    META_NEGATIVE_CONTROL_FEATURES,
    build_meta_historical_dataset,
    premarket_meta_feature_row,
)


def _frame(n=100):
    dates = pd.bdate_range("2025-01-02", periods=n)
    idx = np.arange(n, dtype=float)
    close = 100.0 + idx * 0.12 + np.sin(idx / 5.0)
    open_ = close * (1.0 + 0.0015 * np.cos(idx / 8.0))
    high = np.maximum(open_, close) * 1.005
    low = np.minimum(open_, close) * 0.995
    volume = 1_000_000.0 + idx * 4200.0 + 8000.0 * np.sin(idx / 11.0)
    return pd.DataFrame({"date": dates, "open": open_, "high": high, "low": low, "close": close, "volume": volume})


def test_all_meta_symbolic_states_match_batch_and_premarket_paths():
    raw = _frame()
    target_idx = 80
    target_date = raw.loc[target_idx, "date"]
    batch = build_meta_historical_dataset(raw)
    batch_row = batch.loc[batch["date"] == target_date].iloc[0]
    premkt = premarket_meta_feature_row(raw.iloc[:target_idx].copy(), target_date).iloc[0]

    cols = []
    for values in META_CANDIDATE_FEATURES.values():
        cols.extend(values)
    for values in META_NEGATIVE_CONTROL_FEATURES.values():
        cols.extend(values)
    for col in cols:
        assert str(batch_row[col]) == str(premkt[col]), col
