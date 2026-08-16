import numpy as np
import pandas as pd

from metaalpha.forward_meta import CANDIDATES, MIN_GATE_SESSIONS, evaluate_gate


def _gate_frame(n=MIN_GATE_SESSIONS):
    dates = pd.bdate_range("2026-08-17", periods=n)
    y = (np.arange(n) % 2).astype(int)
    base = np.full(n, 0.50)
    oracle = np.where(y == 1, 0.80, 0.20)
    flat = base.copy()
    returns = np.where(y == 1, 0.005, -0.005)
    return pd.DataFrame(
        {
            "date": dates,
            "same_session_direction": y,
            "same_session_return": returns,
            "baseline_prob": base,
            "cycle_prob": oracle,
            "ziping_prob": flat,
            "qimen_prob": flat,
            "meihua_prob": flat,
            "liuyao_hash_prob": flat,
        }
    )


def test_meta_future_gate_can_select_one_candidate_without_control_alarm():
    gate = evaluate_gate(_gate_frame(), coverage=1.0)
    assert gate["verdict_locked"] is True
    assert gate["negative_control_alarm"] is False
    assert gate["winner"] == "cycle"
    assert gate["candidate_results"]["cycle"]["decision"] == "PASS"
    for branch in ("ziping", "qimen", "meihua"):
        assert gate["candidate_results"][branch]["decision"] == "FAIL"
    assert list(gate["candidate_results"]) == list(CANDIDATES)
