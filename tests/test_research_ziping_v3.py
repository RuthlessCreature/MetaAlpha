import numpy as np
import pandas as pd

from metaalpha.pipeline import build_dataset
from metaalpha.research_ziping_v3 import _joint_route_test


def test_pipeline_emits_route_v3_features():
    raw = pd.DataFrame(
        {
            "date": pd.date_range("2026-08-01", periods=12, freq="D"),
            "close": [100, 101, 99, 100, 102, 103, 101, 104, 105, 104, 106, 107],
        }
    )
    out = build_dataset(raw, include_ziping=True)
    expected = {
        "zpzt_route__v3__route_state",
        "zpzt_route__v3__route_hit_count",
        "zpzt_route__v3__assistant_count",
        "zpzt_route__v3__aggregate_score_defined",
    }
    assert expected.issubset(out.columns)
    assert set(out["zpzt_route__v3__aggregate_score_defined"].unique()) == {0}


def test_joint_route_test_detects_incremental_effect_after_baselines():
    n = 900
    dates = pd.bdate_range("2018-01-02", periods=n)
    route = np.array([i % 3 for i in range(n)])
    selected_use = np.array(["正官" if i % 2 else "正财" for i in range(n)])
    weekday = dates.weekday
    month = dates.month

    # Route level has a large independent effect. Small deterministic baseline
    # components ensure the test must control rather than merely omit them.
    y = (
        (route == 1) * 0.004
        + (route == 2) * -0.003
        + (selected_use == "正官") * 0.0003
        + (weekday == 0) * 0.0002
        + (month == 1) * -0.0002
        + np.sin(np.arange(n) / 13.0) * 0.00015
    )
    df = pd.DataFrame(
        {
            "date": dates,
            "ret_fwd_1": y,
            "zpzt_use__v2__selected_ten_god": selected_use,
            "calendar__v1__weekday": weekday,
            "calendar__v1__month": month,
            "route_test": route,
        }
    )

    row, coefficients = _joint_route_test(
        df,
        "route_test",
        min_level_n=100,
        min_rows=500,
        maxlags=5,
    )
    assert row is not None
    assert row["p_value"] < 0.001
    assert row["delta_r2"] > 0.5
    assert row["rank_deficient"] == 0
    assert len(coefficients) == 2
