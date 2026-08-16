import pandas as pd

from metaalpha.controls import add_deterministic_null_controls, add_shifted_feature


def test_deterministic_null_controls_repeat_exactly():
    df = pd.DataFrame({"date": ["2026-08-14", "2026-08-15", "2026-08-16"]})
    a = add_deterministic_null_controls(df)
    b = add_deterministic_null_controls(df)
    cols = [c for c in a.columns if c.startswith("control__v1__random_")]
    assert a[cols].equals(b[cols])


def test_shifted_feature_does_not_wrap():
    df = pd.DataFrame({"symbol": ["X"] * 3, "x": [1, 2, 3]})
    out = add_shifted_feature(df, "x", shift_rows=1)
    col = "control__v1__shift_1__x"
    assert pd.isna(out.loc[0, col])
    assert out.loc[1, col] == 1
    assert out.loc[2, col] == 2
