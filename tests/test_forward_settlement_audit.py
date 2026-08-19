from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

import metaalpha.forward_settlement_audit as fsa
from metaalpha.forward_meta import ALL_BRANCHES, CANDIDATES, FAMILY_ID, NEGATIVE_CONTROLS, VERSION, _features_for_branch


def _payload(*, late: bool, eligible: bool):
    generated = "2026-08-18T09:47:47+08:00" if late else "2026-08-18T06:10:00+08:00"
    predictions = {model: {"prob_up": 0.55, "best_C": 0.01} for model in ("baseline", *ALL_BRANCHES)}
    return {
        "schema_version": 1,
        "family_id": FAMILY_ID,
        "version": VERSION,
        "date": "2026-08-18",
        "generated_at": generated,
        "session_anchor": "2026-08-18T09:25:00+08:00",
        "forward_start": "2026-08-17",
        "active_after_registration": True,
        "precommitted_before_anchor": not late,
        "confirmatory_eligible": eligible,
        "calendar_status": "candidate_session_unconfirmed",
        "provider": "sina",
        "symbol": "000001",
        "training_last_market_date": "2026-08-17",
        "training_rows": 8684,
        "code_commit": "a" * 40,
        "market_manifest": {"last_date": "2026-08-17", "requested_end": "20260817"},
        "predictions": predictions,
        "branch_states": {
            branch: {feature: "x" for feature in _features_for_branch(branch)}
            for branch in ALL_BRANCHES
        },
        "forecast_labels": {model: "up" for model in predictions},
        "candidate_branches": list(CANDIDATES),
        "negative_controls": list(NEGATIVE_CONTROLS),
    }


def _patch_git(monkeypatch, commit_time: str, touches: int = 1):
    rows = [(str(i) * 40, pd.Timestamp(commit_time)) for i in range(1, touches + 1)]
    monkeypatch.setattr(fsa, "_git_touch_history", lambda path, repo_root: rows)
    monkeypatch.setattr(
        fsa.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )


def test_settlement_tolerates_correctly_declared_late_ineligible(monkeypatch, tmp_path: Path):
    payload = _payload(late=True, eligible=False)
    _patch_git(monkeypatch, "2026-08-18T01:48:35+00:00")
    errors, tolerated = fsa.audit_settlement_git_immutability(tmp_path / "2026-08-18.json", payload, tmp_path)
    assert errors == []
    assert tolerated is True


def test_structural_audit_rejects_late_record_claiming_eligible(tmp_path: Path):
    payload = _payload(late=True, eligible=True)
    errors = fsa.audit_meta_payload(payload, expected_filename_date="2026-08-18")
    assert any("confirmatory_eligible" in err for err in errors)


def test_settlement_still_rejects_post_anchor_commit_for_eligible_record(monkeypatch, tmp_path: Path):
    payload = _payload(late=False, eligible=True)
    _patch_git(monkeypatch, "2026-08-18T01:48:35+00:00")
    errors, tolerated = fsa.audit_settlement_git_immutability(tmp_path / "2026-08-18.json", payload, tmp_path)
    assert tolerated is False
    assert any("eligible record commit" in err for err in errors)


def test_settlement_requires_exactly_one_git_touch(monkeypatch, tmp_path: Path):
    payload = _payload(late=True, eligible=False)
    _patch_git(monkeypatch, "2026-08-18T01:48:35+00:00", touches=2)
    errors, tolerated = fsa.audit_settlement_git_immutability(tmp_path / "2026-08-18.json", payload, tmp_path)
    assert tolerated is False
    assert any("exactly one commit touch" in err for err in errors)


def test_directory_reports_tolerated_ineligible_without_failure(monkeypatch, tmp_path: Path):
    predictions = tmp_path / "predictions"
    predictions.mkdir()
    payload = _payload(late=True, eligible=False)
    (predictions / "2026-08-18.json").write_text(__import__("json").dumps(payload), encoding="utf-8")
    _patch_git(monkeypatch, "2026-08-18T01:48:35+00:00")
    result = fsa.audit_meta_settlement_directory(predictions, repo_root=tmp_path)
    assert result["status"] == "PASS"
    assert result["tolerated_late_ineligible_records"] == ["2026-08-18.json"]
