from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from metaalpha.forward_meta_ledger import (
    TARGET_DIRECTION,
    TARGET_RETURN,
    _market_with_realized_targets,
    build_realization_payload,
    load_realized_records,
    validate_realization_payload,
    write_missing_realizations,
)


def _prediction(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "family_id": "META_FWD_001",
                "date": "2026-08-17",
                "confirmatory_eligible": True,
                "predictions": {"baseline": {"prob_up": 0.5}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _market():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-08-14", "2026-08-17"]),
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [100.0, 102.0],
            "volume": [1_000.0, 1_100.0],
        }
    )


def test_realization_refuses_same_day_before_cutoff(tmp_path):
    prediction = _prediction(tmp_path / "predictions" / "2026-08-17.json")
    row = _market_with_realized_targets(_market()).iloc[-1]
    with pytest.raises(ValueError, match="before 15:30"):
        build_realization_payload(
            prediction,
            row,
            settled_at="2026-08-17T15:10:00+08:00",
        )


def test_realization_locks_return_and_prediction_hash(tmp_path):
    prediction = _prediction(tmp_path / "predictions" / "2026-08-17.json")
    row = _market_with_realized_targets(_market()).iloc[-1]
    payload = build_realization_payload(
        prediction,
        row,
        settled_at="2026-08-17T16:40:00+08:00",
    )
    assert payload["realized_return"] == pytest.approx(0.02)
    assert payload["realized_direction"] == 1
    assert validate_realization_payload(
        payload,
        expected_filename_date="2026-08-17",
        prediction_path=prediction,
    ) == []


def test_existing_realization_is_never_overwritten(tmp_path):
    predictions_dir = tmp_path / "predictions"
    realized_dir = tmp_path / "realized"
    _prediction(predictions_dir / "2026-08-17.json")

    created = write_missing_realizations(
        predictions_dir,
        realized_dir,
        _market(),
        settled_at="2026-08-17T16:40:00+08:00",
    )
    assert [p.name for p in created] == ["2026-08-17.json"]
    original = (realized_dir / "2026-08-17.json").read_bytes()

    revised = _market().copy()
    revised.loc[revised["date"] == pd.Timestamp("2026-08-17"), "close"] = 80.0
    created_again = write_missing_realizations(
        predictions_dir,
        realized_dir,
        revised,
        settled_at="2026-08-18T16:40:00+08:00",
    )
    assert created_again == []
    assert (realized_dir / "2026-08-17.json").read_bytes() == original


def test_realization_detects_prediction_tampering(tmp_path):
    predictions_dir = tmp_path / "predictions"
    realized_dir = tmp_path / "realized"
    prediction = _prediction(predictions_dir / "2026-08-17.json")
    write_missing_realizations(
        predictions_dir,
        realized_dir,
        _market(),
        settled_at="2026-08-17T16:40:00+08:00",
    )

    prediction.write_text('{"family_id":"META_FWD_001","date":"2026-08-17","tampered":true}', encoding="utf-8")
    with pytest.raises(ValueError, match="prediction_sha256"):
        load_realized_records(realized_dir, predictions_dir)


def test_market_target_uses_previous_trading_close():
    out = _market_with_realized_targets(_market())
    row = out.iloc[-1]
    assert row["previous_market_date"] == pd.Timestamp("2026-08-14")
    assert row[TARGET_RETURN] == pytest.approx(0.02)
    assert int(row[TARGET_DIRECTION]) == 1
