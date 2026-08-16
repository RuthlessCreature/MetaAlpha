import pandas as pd

from metaalpha.data_reconcile import compare_provider_frames


def _frame(close_values):
    dates = pd.date_range("2024-01-02", periods=len(close_values), freq="B")
    close = pd.Series(close_values, dtype=float)
    return pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
        }
    )


def test_pairwise_reconciliation_detects_return_disagreement():
    a = _frame([100, 101, 102, 103, 104])
    b = _frame([100, 101, 110, 103, 104])
    metrics, top = compare_provider_frames(a, b, left_name="a", right_name="b")
    assert metrics["common_dates"] == 5
    assert metrics["max_close_abs_diff"] == 8.0
    assert metrics["ret_diff_gt_100bp"] >= 1
    assert not top.empty
    assert {"left_provider", "right_provider", "ret1_abs_diff"}.issubset(top.columns)
