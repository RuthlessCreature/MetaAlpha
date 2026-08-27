import numpy as np
import pandas as pd

from metaalpha.forward_ziping_safe_score import score_forward_experiment


def test_immature_forward_sample_stays_collecting_and_hides_inference():
    # Seven realized rows have positive regression residual degrees of freedom,
    # but the frozen 300-total / 30-signal gate is nowhere near ready. The
    # production scorer should keep collecting and suppress inferential HAC
    # output rather than exposing unstable tiny-sample t/p values.
    dates = pd.bdate_range("2026-08-17", periods=8)
    signals = np.array([1, 0, 0, 0, 0, 1, 0, 0], dtype=int)

    returns = np.array([0.001, -0.002, 0.003, -0.001, 0.002, -0.001, 0.0015])
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
    assert result["total_scored_sessions"] == 7
    assert result["checks"]["sample_ready"] is False
    assert "suppressed" in result["reason"]
    assert np.isnan(result["calendar_adjusted_hac"]["coefficient_bps"])
    assert all(
        np.isnan(model["coefficient_bps"])
        for model in result["shift_null_hac"].values()
    )
