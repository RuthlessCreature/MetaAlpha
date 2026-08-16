import numpy as np
import pandas as pd

from metaalpha.labels import add_forward_labels


def test_forward_returns_are_future_only():
    df = pd.DataFrame(
        {
            "symbol": ["X"] * 4,
            "date": pd.date_range("2026-01-01", periods=4),
            "close": [100.0, 110.0, 121.0, 133.1],
        }
    )
    out = add_forward_labels(df, horizons=(1,))
    assert np.isclose(out.loc[0, "ret_fwd_1"], 0.10)
    assert np.isclose(out.loc[1, "ret_fwd_1"], 0.10)
    assert pd.isna(out.loc[3, "ret_fwd_1"])


def test_groups_do_not_leak_across_symbols():
    df = pd.DataFrame(
        {
            "symbol": ["A", "A", "B", "B"],
            "date": ["2026-01-01", "2026-01-02", "2026-01-01", "2026-01-02"],
            "close": [100.0, 101.0, 200.0, 198.0],
        }
    )
    out = add_forward_labels(df, horizons=(1,))
    a_last = out[(out.symbol == "A") & (out.date == "2026-01-02")].iloc[0]
    b_first = out[(out.symbol == "B") & (out.date == "2026-01-01")].iloc[0]
    assert pd.isna(a_last.ret_fwd_1)
    assert np.isclose(b_first.ret_fwd_1, -0.01)
