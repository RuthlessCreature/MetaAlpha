import numpy as np
import pandas as pd

from metaalpha.validation import evaluate_categorical_feature_hac, evaluate_categorical_family


def test_hac_indicator_coefficient_matches_mean_difference():
    n = 240
    feature = np.tile([0, 1], n // 2)
    # Deterministic small trend + level effect keeps the expected mean difference clear.
    target = np.linspace(-0.02, 0.02, n) + feature * 0.01
    df = pd.DataFrame(
        {
            "date": pd.bdate_range("2020-01-01", periods=n),
            "feature": feature,
            "target": target,
        }
    )

    out = evaluate_categorical_feature_hac(df, "feature", "target", min_n=50, maxlags=5)
    row = out[out["level"] == 1].iloc[0]
    expected = df.loc[df.feature == 1, "target"].mean() - df.loc[df.feature == 0, "target"].mean()
    assert np.isclose(row["mean_difference"], expected)
    assert row["inference"] == "ols_hac"
    assert row["hac_maxlags"] == 5
    assert 0 <= row["p_value"] <= 1


def test_family_hac_applies_family_wide_fdr():
    n = 300
    df = pd.DataFrame(
        {
            "date": pd.bdate_range("2020-01-01", periods=n),
            "a": np.tile([0, 1], n // 2),
            "b": np.tile([0, 1, 2], n // 3),
            "target": np.sin(np.arange(n) / 10.0) * 0.01,
        }
    )
    out = evaluate_categorical_family(
        df,
        ["a", "b"],
        "target",
        family_name="hac_family",
        min_n=30,
        inference="hac",
        hac_maxlags=10,
    )
    assert not out.empty
    assert set(out["inference"]) == {"ols_hac"}
    assert set(out["hac_maxlags"]) == {10}
    assert np.all((out["p_fdr_bh_family"] >= 0) & (out["p_fdr_bh_family"] <= 1))
