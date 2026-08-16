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
    metrics, top, missing = compare_provider_frames(a, b, left_name="a", right_name="b")
    assert metrics["common_dates"] == 5
    assert metrics["max_close_abs_diff"] == 8.0
    assert metrics["ret_diff_gt_100bp"] >= 1
    assert not top.empty
    assert missing.empty
    assert {"left_provider", "right_provider", "ret1_abs_diff"}.issubset(top.columns)


def test_returns_are_computed_after_common_date_alignment():
    a = _frame([100, 101, 102, 103, 104])
    b = _frame([100, 101, 102, 103, 104]).drop(index=2).reset_index(drop=True)

    metrics, top, missing = compare_provider_frames(a, b, left_name="a", right_name="b")

    # The missing date is reported explicitly instead of manufacturing a
    # one-session-vs-two-session return disagreement.
    assert metrics["left_only_dates"] == 1
    assert metrics["right_only_dates"] == 0
    assert len(missing) == 1
    assert missing.iloc[0]["missing_from"] == "b"

    # On the common-date timeline the closes are identical, so returns are too.
    assert metrics["max_close_abs_diff"] == 0.0
    assert metrics["max_ret1_abs_diff"] == 0.0
    assert metrics["ret_diff_gt_1bp"] == 0
