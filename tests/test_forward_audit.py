from __future__ import annotations

from copy import deepcopy

from metaalpha.forward_audit import audit_meta_payload
from metaalpha.forward_meta import ALL_BRANCHES, CANDIDATES, FAMILY_ID, NEGATIVE_CONTROLS, VERSION, _features_for_branch


def _valid_payload():
    predictions = {
        model: {"prob_up": 0.55, "best_C": 0.01}
        for model in ("baseline", *ALL_BRANCHES)
    }
    return {
        "schema_version": 1,
        "family_id": FAMILY_ID,
        "version": VERSION,
        "date": "2026-08-17",
        "generated_at": "2026-08-16T22:15:40+08:00",
        "session_anchor": "2026-08-17T09:25:00+08:00",
        "forward_start": "2026-08-17",
        "active_after_registration": True,
        "precommitted_before_anchor": True,
        "confirmatory_eligible": True,
        "calendar_status": "candidate_session_unconfirmed",
        "provider": "sina",
        "symbol": "000001",
        "training_last_market_date": "2026-08-14",
        "training_rows": 8683,
        "code_commit": "a" * 40,
        "market_manifest": {
            "last_date": "2026-08-14",
            "requested_end": "20260816",
        },
        "predictions": predictions,
        "branch_states": {
            branch: {feature: "x" for feature in _features_for_branch(branch)}
            for branch in ALL_BRANCHES
        },
        "forecast_labels": {model: "up" for model in predictions},
        "candidate_branches": list(CANDIDATES),
        "negative_controls": list(NEGATIVE_CONTROLS),
    }


def test_valid_payload_passes_structural_audit():
    payload = _valid_payload()
    assert audit_meta_payload(payload, expected_filename_date="2026-08-17") == []


def test_eligibility_is_recomputed_not_trusted():
    payload = _valid_payload()
    payload["confirmatory_eligible"] = False
    errors = audit_meta_payload(payload, expected_filename_date="2026-08-17")
    assert any("confirmatory_eligible" in err for err in errors)


def test_late_record_cannot_claim_precommit():
    payload = _valid_payload()
    payload["generated_at"] = "2026-08-17T09:30:00+08:00"
    errors = audit_meta_payload(payload, expected_filename_date="2026-08-17")
    assert any("precommitted_before_anchor" in err for err in errors)
    assert any("confirmatory_eligible" in err for err in errors)


def test_training_cutoff_must_precede_target():
    payload = _valid_payload()
    payload["training_last_market_date"] = "2026-08-17"
    errors = audit_meta_payload(payload, expected_filename_date="2026-08-17")
    assert any("training_last_market_date" in err for err in errors)


def test_missing_candidate_prediction_fails():
    payload = _valid_payload()
    del payload["predictions"]["meihua"]
    errors = audit_meta_payload(payload, expected_filename_date="2026-08-17")
    assert any("predictions: model set mismatch" in err for err in errors)


def test_filename_date_mismatch_fails():
    payload = _valid_payload()
    errors = audit_meta_payload(payload, expected_filename_date="2026-08-18")
    assert any("does not match filename" in err for err in errors)


def test_branch_feature_set_is_frozen():
    payload = _valid_payload()
    payload = deepcopy(payload)
    payload["branch_states"]["cycle"]["cycle__v1__invented_after_result"] = "x"
    errors = audit_meta_payload(payload, expected_filename_date="2026-08-17")
    assert any("branch_states.cycle: feature set mismatch" in err for err in errors)
