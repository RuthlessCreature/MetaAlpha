import numpy as np
import pandas as pd

from metaalpha.research_ganzhi_vol import (
    BlockSpec,
    _build_dataset,
    _fit_block,
)


def test_market_baseline_is_lagged_to_t_minus_1():
    # Known returns include a huge move at t. The baseline on row t must still
    # use the previous session's absolute return, never the same-day move.
    returns = [0.01, -0.02, 0.03, -0.04, 0.05, 0.50, 0.01, 0.02, 0.01, -0.01,
               0.02, 0.01, -0.02, 0.01, 0.02, -0.01, 0.01, 0.02, -0.01, 0.01,
               0.02, 0.01, -0.01, 0.02, 0.01, -0.02, 0.01, 0.02, 0.01, -0.01]
    close = [100.0]
    for r in returns:
        close.append(close[-1] * (1.0 + r))
    raw = pd.DataFrame(
        {
            "date": pd.bdate_range("2022-01-03", periods=len(close)),
            "close": close,
            "symbol": "INDEX_000001",
        }
    )
    out = _build_dataset(raw)
    # Row 6 return is 50%; its lagged baseline must equal abs(row 5 return)=5%.
    assert np.isclose(out.loc[6, "ret_1"], 0.50)
    assert np.isclose(out.loc[6, "abs_ret_1_lag1"], 0.05)


def test_mod5_subsamples_have_nonoverlapping_future_windows():
    # For start rows separated by five trading sessions, t+1..t+5 windows are disjoint.
    session_index = np.arange(40)
    for residue in range(5):
        starts = session_index[session_index % 5 == residue]
        for left, right in zip(starts[:-1], starts[1:]):
            left_window = set(range(left + 1, left + 6))
            right_window = set(range(right + 1, right + 6))
            assert left_window.isdisjoint(right_window)


def _synthetic_model_frame(n: int = 1200) -> pd.DataFrame:
    dates = pd.bdate_range("2015-01-05", periods=n)
    phase = np.arange(n) % 4
    x = np.sin(np.arange(n) / 31.0)
    log_back5 = -4.6 + 0.05 * x
    log_back20 = -4.5 + 0.03 * np.cos(np.arange(n) / 41.0)
    abs_ret = 0.008 + 0.001 * np.sin(np.arange(n) / 17.0)
    time = np.arange(n) / float(n - 1)
    y = (
        -4.4
        + 0.30 * (phase == 1)
        - 0.25 * (phase == 3)
        + 0.25 * log_back5
        + 0.15 * log_back20
        + 2.0 * abs_ret
        + 0.02 * time
        + np.sin(np.arange(n) / 13.0) * 0.015
    )
    return pd.DataFrame(
        {
            "date": dates,
            "log_vol_fwd_5": y,
            "log_vol_back_5_lag1": log_back5,
            "log_vol_back_20_lag1": log_back20,
            "abs_ret_1_lag1": abs_ret,
            "normalized_time": time,
            "normalized_time_squared": time ** 2,
            "calendar_weekday": dates.weekday.astype(str),
            "calendar_month": dates.month.astype(str),
            "synthetic_phase": phase,
        }
    )


def test_joint_cycle_block_detects_incremental_effect_after_strict_baseline():
    df = _synthetic_model_frame()
    block = BlockSpec("synthetic_phase", "categorical", ("synthetic_phase",))
    row, coefs = _fit_block(
        df,
        block,
        min_level_n=20,
        min_rows=500,
        hac_maxlags=20,
    )
    assert row is not None
    assert row["valid_inference"] == 1
    assert row["p_value"] < 1e-6
    assert row["delta_r2"] > 0.5
    assert len(coefs) == 3


def test_joint_cycle_block_rejects_exact_baseline_collinearity():
    df = _synthetic_model_frame()
    df["synthetic_month"] = df["calendar_month"]
    block = BlockSpec("synthetic_month", "categorical", ("synthetic_month",))
    row, coefs = _fit_block(
        df,
        block,
        min_level_n=20,
        min_rows=500,
        hac_maxlags=20,
    )
    assert row is not None
    assert row["valid_inference"] == 0
    assert row["invalid_reason"] == "design_matrix_rank_deficient"
    assert np.isnan(row["p_value"])
    assert coefs.empty
