import numpy as np
import pandas as pd

from metaalpha.research_qimen_market import BlockSpec, _build_dataset, _fit_block


def test_qimen_market_baseline_uses_only_t_minus_1_or_earlier():
    # A huge return on row 7 must not leak into its own 09:25 baseline.
    returns = [0.01, -0.02, 0.03, -0.01, 0.02, 0.04, 0.50, -0.02,
               0.01, 0.02, -0.01, 0.01, 0.02, -0.01, 0.02, 0.01,
               -0.02, 0.01, 0.02, -0.01, 0.01, 0.02, -0.01, 0.01,
               0.02, -0.01, 0.01, 0.02, -0.01, 0.01]
    close = [100.0]
    for r in returns:
        close.append(close[-1] * (1.0 + r))
    raw = pd.DataFrame({
        "date": pd.bdate_range("2026-01-05", periods=len(close)),
        "close": close,
        "symbol": "INDEX_000001",
    })
    out = _build_dataset(raw)
    assert np.isclose(out.loc[7, "ret_session_t"], 0.50)
    assert np.isclose(out.loc[7, "ret_session_lag1"], 0.04)


def _synthetic_frame(n: int = 1200) -> pd.DataFrame:
    dates = pd.bdate_range("2014-01-06", periods=n)
    block = np.array([i % 4 for i in range(n)])
    lag = np.sin(np.arange(n) / 17.0) * 0.001
    vol5 = 0.01 + np.sin(np.arange(n) / 31.0) * 0.001
    vol20 = 0.012 + np.cos(np.arange(n) / 43.0) * 0.001
    time = np.arange(n) / float(n - 1)
    y = (
        (block == 1) * 0.004
        - (block == 3) * 0.003
        + 0.20 * lag
        + 0.10 * vol5
        - 0.10 * vol20
        + (dates.weekday == 0) * 0.0002
        + (dates.month == 1) * -0.0002
        + np.sin(np.arange(n) / 11.0) * 0.00015
    )
    return pd.DataFrame({
        "date": dates,
        "ret_session_t": y,
        "ret_session_lag1": lag,
        "vol_back_5_lag1": vol5,
        "vol_back_20_lag1": vol20,
        "normalized_time": time,
        "normalized_time_squared": time ** 2,
        "calendar_weekday": dates.weekday.astype(str),
        "calendar_month": dates.month.astype(str),
        "synthetic_qimen": block,
    })


def test_joint_qimen_block_detects_incremental_effect():
    df = _synthetic_frame()
    block = BlockSpec("synthetic_qimen", "synthetic_qimen")
    row, coefs = _fit_block(df, block, min_level_n=50, min_rows=500)
    assert row is not None
    assert row["valid_inference"] == 1
    assert row["p_value"] < 1e-6
    assert row["delta_r2"] > 0.5
    assert len(coefs) == 3
    assert set(coefs["level"]) == {"1", "2", "3"}


def test_joint_qimen_block_invalidates_exact_calendar_collinearity():
    df = _synthetic_frame()
    df["synthetic_qimen"] = df["calendar_month"]
    block = BlockSpec("synthetic_qimen", "synthetic_qimen")
    row, coefs = _fit_block(df, block, min_level_n=50, min_rows=500)
    assert row is not None
    assert row["valid_inference"] == 0
    assert row["invalid_reason"] == "design_matrix_rank_deficient"
    assert np.isnan(row["p_value"])
    assert coefs.empty
