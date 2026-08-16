from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

from .forward_meta import FAMILY_ID, FORWARD_START, TZ_SHANGHAI


# The first record was intentionally bootstrapped on Sunday for Monday 2026-08-17
# before the family became active. It is the sole allowed prior-civil-day record.
GRANDFATHER_TARGET = pd.Timestamp("2026-08-17")
GRANDFATHER_GENERATED_DATE = pd.Timestamp("2026-08-16")


def audit_daily_refit_payload(payload: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if payload.get("family_id") != FAMILY_ID:
        return errors
    try:
        target = pd.Timestamp(payload["date"]).normalize().tz_localize(None)
        generated = pd.Timestamp(payload["generated_at"])
    except Exception as exc:
        return [f"date/generated_at: invalid: {exc}"]
    if generated.tzinfo is None:
        return ["generated_at: must be timezone-aware"]
    generated_day = generated.tz_convert(TZ_SHANGHAI).normalize().tz_localize(None)

    if target == GRANDFATHER_TARGET and generated_day == GRANDFATHER_GENERATED_DATE:
        return []
    if target >= FORWARD_START and generated_day != target:
        errors.append(
            "daily_refit: target date must equal Shanghai generation date; "
            f"got target={target.date()} generated_day={generated_day.date()}"
        )
    return errors


def audit_directory(predictions_dir: Path) -> dict[str, object]:
    failures: dict[str, list[str]] = {}
    records = 0
    for path in sorted(predictions_dir.glob("*.json")):
        records += 1
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures[path.name] = [f"json: {exc}"]
            continue
        errors = audit_daily_refit_payload(payload)
        if errors:
            failures[path.name] = errors
    return {
        "schema_version": 1,
        "family_id": FAMILY_ID,
        "records": records,
        "status": "PASS" if not failures else "FAIL",
        "grandfather": {
            "target": GRANDFATHER_TARGET.strftime("%Y-%m-%d"),
            "generated_day": GRANDFATHER_GENERATED_DATE.strftime("%Y-%m-%d"),
        },
        "failures": failures,
        "rule": "After the first bootstrap, each prediction must be generated on its target Shanghai civil date so the frozen expanding-daily-refit policy cannot be bypassed by bulk early precommitment.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit META_FWD_001 daily expanding-refit cadence")
    parser.add_argument("--predictions-dir", type=Path, required=True)
    args = parser.parse_args()
    result = audit_directory(args.predictions_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
