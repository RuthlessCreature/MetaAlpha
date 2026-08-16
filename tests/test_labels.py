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


def test_forward_volatility_is_exactly_t_plus_1_through_t_plus_h():
    # Construct closes from known one-session returns. At row 0, vol_fwd_5
    # must use 1%,2%,3%,4%,5%; row 1 must use 2%,3%,4%,5%,6%.
    one_day_returns = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06]
    closes = [100.0]
    for r in one_day_returns:
        closes.append(closes[-1] * (1.0 + r))

    df = pd.DataFrame(
        {
            "symbol": ["X"] * len(closes),
            "date": pd.date_range("2026-01-01", periods=len(closes)),
            "close": closes,
        }
    )
    out = add_forward_labels(df)

    expected_0 = np.std([0.01, 0.02, 0.03, 0.04, 0.05], ddof=1)
    expected_1 = np.std([0.02, 0.03, 0.04, 0.05, 0.06], ddof=1)
    assert np.isclose(out.loc[0, "vol_fwd_5"], expected_0)
    assert np.isclose(out.loc[1, "vol_fwd_5"], expected_1)
    assert pd.isna(out.loc[2, "vol_fwd_5"])
