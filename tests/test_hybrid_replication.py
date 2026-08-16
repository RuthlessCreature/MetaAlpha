import numpy as np
import pandas as pd

from metaalpha.market_baseline import add_market_baseline_features
from metaalpha.research_hybrid_replication import prepare_replication_raw, replication_decision


def test_replication_requires_three_of_four_indices_per_model():
    rows = []
    for index_id, cycle_pass, ziping_pass in [
        ("a", 1, 1),
        ("b", 1, 0),
        ("c", 1, 1),
        ("d", 0, 0),
    ]:
        rows.append({"index_id": index_id, "model_id": "cycle", "gate_pass": cycle_pass})
        rows.append({"index_id": index_id, "model_id": "ziping", "gate_pass": ziping_pass})
    out = replication_decision(pd.DataFrame(rows)).set_index("model_id")
    assert out.loc["cycle", "indices_passed"] == 3
    assert out.loc["cycle", "replication_pass"] == 1
    assert out.loc["ziping", "indices_passed"] == 2
    assert out.loc["ziping", "replication_pass"] == 0


def test_volume_qc_preserves_price_calendar_and_targets():
    dates = pd.bdate_range("2024-01-02", periods=40)
    close = 100.0 + np.arange(40, dtype=float)
    raw = pd.DataFrame(
        {
            "date": dates,
            "open": close - 0.2,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(40, 1_000_000.0),
        }
    )
    raw.loc[20, "volume"] = 0.0

    prepared, bad_count = prepare_replication_raw(raw)
    assert bad_count == 1
    assert len(prepared) == len(raw)
    assert prepared["date"].equals(raw["date"])
    assert prepared["close"].equals(raw["close"])
    assert pd.isna(prepared.loc[20, "volume"])

    features = add_market_baseline_features(prepared)
    # Price targets remain one-session returns on the untouched calendar.
    assert np.isclose(features.loc[20, "same_session_return"], close[20] / close[19] - 1.0)
    assert np.isclose(features.loc[21, "same_session_return"], close[21] / close[20] - 1.0)
    # Volume-derived predictors become missing instead of being fabricated.
    assert pd.isna(features.loc[21, "volume_log_change_lag_1"])
