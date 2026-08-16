from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

from .forward_audit import _git_touch_history
from .forward_meta_ledger import (
    FAMILY_ID,
    SETTLEMENT_HOUR,
    SETTLEMENT_MINUTE,
    TZ_SHANGHAI,
    validate_realization_payload,
)


def audit_realized_directory(
    realized_dir: Path,
    predictions_dir: Path,
    *,
    repo_root: Path | None = None,
    verify_git_history: bool = True,
) -> dict[str, object]:
    failures: dict[str, list[str]] = {}
    records = 0

    for path in sorted(realized_dir.glob("*.json")):
        records += 1
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures[path.name] = [f"json: {exc}"]
            continue

        prediction_path = predictions_dir / f"{payload.get('date', path.stem)}.json"
        errors = validate_realization_payload(
            payload,
            expected_filename_date=path.stem,
            prediction_path=prediction_path,
        )

        if verify_git_history:
            if repo_root is None:
                errors.append("git_history: repo_root required when enabled")
            else:
                try:
                    touches = _git_touch_history(path, repo_root)
                except Exception as exc:
                    errors.append(f"git_history: {exc}")
                    touches = []
                if len(touches) != 1:
                    errors.append(f"git_history: realized file must have exactly one commit touch, got {len(touches)}")
                elif touches:
                    _, commit_time = touches[0]
                    try:
                        date = pd.Timestamp(payload["date"]).normalize().tz_localize(TZ_SHANGHAI)
                        cutoff = date.replace(hour=SETTLEMENT_HOUR, minute=SETTLEMENT_MINUTE)
                        if commit_time < cutoff:
                            errors.append(
                                f"git_history: realized commit {commit_time.isoformat()} precedes settlement cutoff {cutoff.isoformat()}"
                            )
                    except Exception as exc:
                        errors.append(f"git_history: cannot validate settlement cutoff: {exc}")

        if errors:
            failures[path.name] = sorted(set(errors))

    return {
        "schema_version": 1,
        "family_id": FAMILY_ID,
        "records": records,
        "git_history_verified": bool(verify_git_history),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "note": "Realized records are append-only outcome snapshots; later source revisions do not rewrite prior locked outcomes.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit immutable META_FWD_001 realized outcome ledger")
    parser.add_argument("--realized-dir", type=Path, required=True)
    parser.add_argument("--predictions-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--skip-git-history", action="store_true")
    args = parser.parse_args()

    result = audit_realized_directory(
        args.realized_dir,
        args.predictions_dir,
        repo_root=args.repo_root,
        verify_git_history=not args.skip_git_history,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
