from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pandas as pd

from .forward_audit import (
    _SHA40,
    _aware_timestamp,
    _date_value,
    _git_touch_history,
    audit_meta_payload,
)
from .forward_meta import FAMILY_ID, FORWARD_START, _anchor


def audit_settlement_git_immutability(
    path: Path,
    payload: dict[str, Any],
    repo_root: Path,
) -> tuple[list[str], bool]:
    """Audit git immutability for settlement without erasing known incidents.

    Settlement must be able to coexist with a prediction record that was
    generated/committed after its anchor *only when* the payload independently
    and correctly declares that record confirmatory-ineligible. Such a record
    remains permanently descriptive and can never enter the eligible ledger.

    Eligible records retain the strict before-anchor git-timing requirement.
    Every record, eligible or not, must still have exactly one path touch and a
    reachable stored code commit.

    Returns ``(errors, tolerated_late_ineligible)``.
    """
    errors: list[str] = []
    tolerated_late_ineligible = False

    try:
        touches = _git_touch_history(path, repo_root)
    except Exception as exc:
        return [f"git_history: {exc}"], False

    if len(touches) != 1:
        return [f"git_history: prediction file must have exactly one commit touch, got {len(touches)}"], False

    _, commit_time = touches[0]
    date = _date_value(payload.get("date"), "date", errors)
    if date is not None:
        anchor = pd.Timestamp(_anchor(date))
        if commit_time.tzinfo is None:
            errors.append("git_history: commit time is not timezone-aware")
        elif commit_time >= anchor:
            if bool(payload.get("confirmatory_eligible")):
                errors.append(
                    f"git_history: eligible record commit {commit_time.isoformat()} is not before anchor {anchor.isoformat()}"
                )
            else:
                tolerated_late_ineligible = True

    code_commit = str(payload.get("code_commit", ""))
    if _SHA40.fullmatch(code_commit):
        proc = subprocess.run(
            ["git", "cat-file", "-e", f"{code_commit}^{{commit}}"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            errors.append("git_history: stored code_commit is not reachable as a commit in this checkout")

    return errors, tolerated_late_ineligible


def audit_meta_settlement_directory(
    predictions_dir: Path,
    *,
    repo_root: Path | None = None,
    verify_git_history: bool = True,
) -> dict[str, Any]:
    """Settlement-safe audit of the immutable META_FWD_001 prediction ledger.

    Structural eligibility is still recomputed rather than trusted. The only
    difference from the strict prediction audit is that a correctly declared
    ineligible record may have a post-anchor git commit without blocking
    settlement of other eligible records.
    """
    failures: dict[str, list[str]] = {}
    records = 0
    independently_eligible = 0
    seen_dates: set[str] = set()
    tolerated_late_ineligible: list[str] = []

    for path in sorted(predictions_dir.glob("*.json")):
        records += 1
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures[path.name] = [f"json: {exc}"]
            continue

        errors = audit_meta_payload(payload, expected_filename_date=path.stem)
        date_text = str(payload.get("date", ""))
        if date_text in seen_dates:
            errors.append("date: duplicate payload date in prediction directory")
        seen_dates.add(date_text)

        date = _date_value(payload.get("date"), "date", errors)
        generated = _aware_timestamp(payload.get("generated_at"), "generated_at", errors)
        if date is not None and generated is not None:
            if date >= FORWARD_START and generated < pd.Timestamp(_anchor(date)):
                independently_eligible += 1

        if verify_git_history:
            if repo_root is None:
                errors.append("git_history: repo_root required when history verification is enabled")
            else:
                git_errors, tolerated = audit_settlement_git_immutability(path, payload, repo_root)
                errors.extend(git_errors)
                if tolerated and not git_errors:
                    tolerated_late_ineligible.append(path.name)

        if errors:
            failures[path.name] = sorted(set(errors))

    return {
        "schema_version": 1,
        "family_id": FAMILY_ID,
        "audit_mode": "settlement",
        "records": records,
        "independently_eligible_records": independently_eligible,
        "git_history_verified": bool(verify_git_history),
        "tolerated_late_ineligible_records": tolerated_late_ineligible,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "note": (
            "Known post-anchor records are tolerated only when structural audit independently confirms "
            "confirmatory_eligible=false; eligible records remain subject to strict pre-anchor git timing."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Settlement-safe audit of immutable META_FWD_001 prediction records")
    parser.add_argument("--predictions-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--skip-git-history", action="store_true")
    args = parser.parse_args()

    result = audit_meta_settlement_directory(
        args.predictions_dir,
        repo_root=args.repo_root,
        verify_git_history=not args.skip_git_history,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
