from metaalpha.forward_daily_refit_audit import audit_daily_refit_payload


def test_first_bootstrap_is_only_prior_day_grandfather():
    payload = {
        "family_id": "META_FWD_001",
        "date": "2026-08-17",
        "generated_at": "2026-08-16T22:15:40+08:00",
    }
    assert audit_daily_refit_payload(payload) == []


def test_normal_same_shanghai_day_passes():
    payload = {
        "family_id": "META_FWD_001",
        "date": "2026-08-18",
        "generated_at": "2026-08-18T08:11:00+08:00",
    }
    assert audit_daily_refit_payload(payload) == []


def test_bulk_early_future_precommit_fails():
    payload = {
        "family_id": "META_FWD_001",
        "date": "2026-08-25",
        "generated_at": "2026-08-18T08:11:00+08:00",
    }
    errors = audit_daily_refit_payload(payload)
    assert any("daily_refit" in error for error in errors)
