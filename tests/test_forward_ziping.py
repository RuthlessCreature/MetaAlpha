from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from metaalpha.forward_ziping import (
    FEATURE_LEVEL,
    HYPOTHESIS_ID,
    ForwardGate,
    generate_signal_record,
    score_forward_experiment,
    write_signal_record,
)


TZ = ZoneInfo("Asia/Shanghai")


def test_signal_record_marks_pre_anchor_eligibility():
    before = generate_signal_record(
        "2026-08-17",
        generated_at=datetime(2026, 8, 17, 8, 0, tzinfo=TZ),
    )
    after = generate_signal_record(
        "2026-08-17",
        generated_at=datetime(2026, 8, 17, 10, 0, tzinfo=TZ),
    )

    assert before["hypothesis_id"] == HYPOTHESIS_ID
    assert before["registered_level"] == FEATURE_LEVEL
    assert before["precommitted_before_anchor"] is True
    assert before["confirmatory_eligible"] is True
    assert after["precommitted_before_anchor"] is False
    assert after["confirmatory_eligible"] is False
    assert set(before["pillars"]) == {"year", "month", "day", "time"}


def test_signal_file_is_immutable(tmp_path: Path):
    path = tmp_path / "2026-08-17.json"
    write_signal_record(
        "2026-08-17",
        path,
        generated_at=datetime(2026, 8, 17, 8, 0, tzinfo=TZ),
    )
    try:
        write_signal_record(
            "2026-08-17",
            path,
            generated_at=datetime(2026, 8, 17, 8, 1, tzinfo=TZ),
        )
    except FileExistsError:
        pass
    else:
        raise AssertionError("existing precommit must never be overwritten")


def test_forward_gate_can_confirm_strong_synthetic_effect():
    n = 90
    dates = pd.bdate_range("2026-08-17", periods=n)
    signals = np.array([1 if i % 3 == 0 else 0 for i in range(n)], dtype=int)

    # Create next-session returns with a large positive signal effect plus a
    # deterministic small alternating component. The final signal cannot be
    # scored because its next close is unavailable, matching real operation.
    returns = np.array([
        (0.004 if signals[i] else -0.0005) + (0.0001 if i % 2 else -0.0001)
        for i in range(n - 1)
    ])
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
    result = score_forward_experiment(
        market,
        signal_df,
        gate=ForwardGate(
            min_total_sessions=60,
            min_signal_sessions=20,
            min_effect_bps=10.0,
            one_sided_alpha=0.025,
            hac_maxlags=5,
        ),
    )

    assert result["total_scored_sessions"] == n - 1
    assert result["signal_sessions"] >= 20
    assert result["calendar_adjusted_hac"]["coefficient_bps"] > 10.0
    assert result["calendar_adjusted_hac"]["p_one_sided_positive"] <= 0.025
    assert result["status"] == "CONFIRMED_FORWARD_CANDIDATE"
