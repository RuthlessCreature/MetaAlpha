import numpy as np
import pandas as pd

from metaalpha.forward_hybrid import MIN_GATE_SESSIONS, _settle, evaluate_gate


def _gate_frame(n=MIN_GATE_SESSIONS):
    rng = np.random.default_rng(123)
    dates = pd.bdate_range("2026-08-17", periods=n)
    latent = rng.normal(size=n)
    p_true = 1.0 / (1.0 + np.exp(-0.5 * latent))
    y = rng.binomial(1, p_true)
    base = np.clip(0.50 + 0.03 * latent, 0.05, 0.95)
    cycle = np.clip(0.50 + 0.18 * latent, 0.05, 0.95)
    ziping = np.full(n, 0.50)
    returns = np.where(y == 1, 0.005, -0.005)
    return pd.DataFrame(
        {
            "date": dates,
            "same_session_direction": y,
            "same_session_return": returns,
            "baseline_prob": base,
            "cycle_prob": cycle,
            "ziping_prob": ziping,
        }
    )


def test_future_gate_is_model_specific_and_locked_shape():
    gate = evaluate_gate(_gate_frame(), coverage=1.0)
    assert gate["verdict_locked"] is True
    assert gate["sample_sessions"] == 500
    assert gate["models"]["cycle"]["gate_pass"] is True
    assert gate["models"]["cycle"]["decision"] == "PASS"
    assert gate["models"]["ziping"]["gate_pass"] is False
    assert gate["models"]["ziping"]["decision"] == "FAIL"


def test_settlement_excludes_nontrading_and_ineligible_records():
    market_dates = pd.to_datetime(["2026-08-17", "2026-08-18", "2026-08-20"])
    market = pd.DataFrame(
        {
            "date": market_dates,
            "open": [100, 101, 102],
            "high": [101, 102, 103],
            "low": [99, 100, 101],
            "close": [100, 101, 103],
            "volume": [1_000_000, 1_100_000, 1_200_000],
        }
    )
    records = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20"]),
            "confirmatory_eligible": [True, True, True, False],
            "baseline_prob": [0.5, 0.5, 0.5, 0.5],
            "cycle_prob": [0.55, 0.55, 0.55, 0.55],
            "ziping_prob": [0.52, 0.52, 0.52, 0.52],
        }
    )
    settled, meta = _settle(market, records)
    # 17th has no prior return in this truncated market frame; 18th settles.
    assert settled["date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-08-18"]
    assert meta["eligible_records"] == 3
