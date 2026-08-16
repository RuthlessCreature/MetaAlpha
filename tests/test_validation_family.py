import numpy as np
import pandas as pd

from metaalpha.validation import evaluate_categorical_family


def test_family_fdr_is_applied_across_all_feature_levels():
    n = 240
    df = pd.DataFrame(
        {
            "a": np.tile([0, 1], n // 2),
            "b": np.tile([0, 1, 2], n // 3),
            "target": np.linspace(-1.0, 1.0, n),
        }
    )
    out = evaluate_categorical_family(
        df,
        ["a", "b"],
        "target",
        family_name="test_family",
        min_n=20,
    )
    assert not out.empty
    assert set(out["family"]) == {"test_family"}
    assert "p_fdr_bh_family" in out.columns
    assert np.all((out["p_fdr_bh_family"] >= 0) & (out["p_fdr_bh_family"] <= 1))
    assert set(out["feature"]) == {"a", "b"}
