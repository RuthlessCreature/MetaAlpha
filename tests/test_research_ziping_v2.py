import pandas as pd

from metaalpha.pipeline import build_dataset
from metaalpha.research_ziping_v2 import _slice_and_purge


def test_pipeline_emits_ziping_use_v2_features():
    raw = pd.DataFrame(
        {
            "date": pd.date_range("2026-08-10", periods=8, freq="D"),
            "close": [100, 101, 100, 102, 103, 104, 103, 105],
        }
    )
    out = build_dataset(raw, include_ziping=True)
    expected = {
        "zpzt_use__v2__selected_ten_god",
        "zpzt_use__v2__selection_mode",
        "zpzt_use__v2__use_change_detected",
        "zpzt_use__v2__composition_mode",
        "zpzt_use__v2__aggregate_fortune_score_defined",
    }
    assert expected.issubset(out.columns)
    assert set(out["zpzt_use__v2__aggregate_fortune_score_defined"].unique()) == {0}


def test_era_slice_purges_last_target_horizon_row():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2020-12-28", periods=7, freq="D"),
            "ret_fwd_1": range(7),
        }
    )
    part, info = _slice_and_purge(
        df,
        start="2020-12-29",
        end="2021-01-02",
        horizon=1,
    )
    assert info.rows_before_purge == 5
    assert info.rows_after_purge == 4
    assert part["date"].max() == pd.Timestamp("2021-01-01")
