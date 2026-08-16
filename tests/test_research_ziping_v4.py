import numpy as np
import pandas as pd

from metaalpha.pipeline import build_dataset
from metaalpha.research_ziping_v4 import _joint_feature_test


def test_pipeline_emits_structure_and_route_v4_features():
    raw = pd.DataFrame(
        {
            "date": pd.date_range("2026-08-01", periods=12, freq="D"),
            "close": [100, 101, 99, 100, 102, 103, 101, 104, 105, 104, 106, 107],
        }
    )
    out = build_dataset(raw, include_ziping=True)
    expected = {
        "zpzt_structure__v4__wealth_resource_position_resolution",
        "zpzt_structure__v4__support_profile",
        "zpzt_route__v4__route_state",
        "zpzt_route__v4__resolved_from_position_count",
    }
    assert expected.issubset(out.columns)
    assert set(out["zpzt_structure__v4__aggregate_strength_score_defined"].unique()) == {0}
    assert set(out["zpzt_route__v4__aggregate_score_defined"].unique()) == {0}


def _synthetic_base(n: int = 900) -> pd.DataFrame:
    dates = pd.bdate_range("2018-01-02", periods=n)
    use = np.array(["正财" if i % 2 == 0 else "正官" for i in range(n)])
    route = np.array(["route_hit" if i % 4 else "route_unresolved" for i in range(n)])
    return pd.DataFrame(
        {
            "date": dates,
            "zpzt_use__v2__selected_ten_god": use,
            "zpzt_route__v3__route_state": route,
            "calendar__v1__weekday": dates.weekday,
            "calendar__v1__month": dates.month,
        }
    )


def test_v4_joint_test_detects_incremental_effect_after_v2_v3_calendar_baseline():
    n = 900
    df = _synthetic_base(n)
    v4 = np.array([i % 3 for i in range(n)])
    use = df["zpzt_use__v2__selected_ten_god"].to_numpy()
    route = df["zpzt_route__v3__route_state"].to_numpy()
    weekday = df["calendar__v1__weekday"].to_numpy()
    month = df["calendar__v1__month"].to_numpy()

    df["ret_fwd_1"] = (
        (v4 == 1) * 0.0035
        + (v4 == 2) * -0.0025
        + (use == "正官") * 0.0002
        + (route == "route_hit") * 0.00015
        + (weekday == 0) * 0.0001
        + (month == 1) * -0.0001
        + np.sin(np.arange(n) / 17.0) * 0.0001
    )
    df["v4_test"] = v4

    row, coefs = _joint_feature_test(
        df,
        "v4_test",
        min_level_n=100,
        min_rows=500,
        maxlags=5,
    )
    assert row is not None
    assert row["valid_inference"] == 1
    assert row["p_value"] < 0.001
    assert row["delta_r2"] > 0.5
    assert row["rank_deficient"] == 0
    assert row["constraint_cov_rank"] == row["constraint_count"]
    assert len(coefs) == 2


def test_v4_joint_test_invalidates_feature_collinear_with_frozen_baseline():
    n = 900
    df = _synthetic_base(n)
    df["ret_fwd_1"] = np.sin(np.arange(n) / 11.0) * 0.001
    # Exact categorical copy of the frozen v3 route-state baseline. Its dummy
    # block contributes no independently identifiable column and must never be
    # assigned a usable Wald p-value/FDR entry.
    df["v4_collinear"] = df["zpzt_route__v3__route_state"]

    row, coefs = _joint_feature_test(
        df,
        "v4_collinear",
        min_level_n=100,
        min_rows=500,
        maxlags=5,
    )
    assert row is not None
    assert row["valid_inference"] == 0
    assert row["rank_deficient"] == 1
    assert row["invalid_reason"] == "design_matrix_rank_deficient"
    assert np.isnan(row["p_value"])
    assert coefs.empty
