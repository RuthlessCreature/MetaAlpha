import numpy as np
import pandas as pd

from metaalpha.forward_ziping_safe_score import score_forward_experiment


def test_tiny_forward_sample_stays_collecting_instead_of_crashing():
    # Six realized rows are enough to saturate the weekday/calendar design in
    # the early forward experiment and previously triggered nobs-k_params == 0
    # inside statsmodels HAC finite-sample correction.
    dates = pd.bdate_range("2026-08-17", periods=7)
    signals = np.array([1, 0, 0, 0, 0, 1, 0], dtype=int)

    returns = np.array([0.001, -0.002, 0.003, -0.001, 0.002, -0.001])
    close = [100.0]
    for r in returns:
        close.append(close[-1] * (1.0 + r))

    market = pd.DataFrame({"date": dates, "close": close, "symbol": "INDEX_000001"})
    signal_df = pd.DataFrame(
        {
            "date": dates,
            "signal": signals,
            "confirmatory_eligible": True,
        }
    )

    result = score_forward_experiment(market, signal_df)

    assert result["status"] == "COLLECTING"
    assert result["total_scored_sessions"] == 6
    assert result["checks"]["sample_ready"] is False
    assert np.isnan(result["calendar_adjusted_hac"]["coefficient_bps"])
