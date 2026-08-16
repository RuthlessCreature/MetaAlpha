from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd

from .forward_meta import (
    ALL_BRANCHES,
    CANDIDATES,
    FAMILY_ID,
    FORWARD_START,
    NEGATIVE_CONTROLS,
    PROVIDER,
    SYMBOL,
    VERSION,
    _anchor,
    _features_for_branch,
)


ALLOWED_C = {0.01, 0.1, 1.0, 10.0}
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _aware_timestamp(value: Any, field: str, errors: list[str]) -> pd.Timestamp | None:
    try:
        ts = pd.Timestamp(value)
    except Exception as exc:
        errors.append(f"{field}: invalid timestamp: {exc}")
        return None
    if ts.tzinfo is None:
        errors.append(f"{field}: timestamp must be timezone-aware")
        return None
    return ts


def _date_value(value: Any, field: str, errors: list[str]) -> pd.Timestamp | None:
    try:
        return pd.Timestamp(value).normalize().tz_localize(None)
    except Exception as exc:
        errors.append(f"{field}: invalid date: {exc}")
        return None


def audit_meta_payload(payload: dict[str, Any], *, expected_filename_date: str | None = None) -> list[str]:
    """Validate a META_FWD_001 record without trusting its eligibility flags.

    This function is deliberately independent of market outcomes. It validates
    record identity, timing, training cutoff, candidate-family completeness and
    the internal consistency of stored probability/label fields.
    """
    errors: list[str] = []

    if payload.get("schema_version") != 1:
        errors.append("schema_version: expected 1")
    if payload.get("family_id") != FAMILY_ID:
        errors.append(f"family_id: expected {FAMILY_ID}")
    if payload.get("version") != VERSION:
        errors.append(f"version: expected {VERSION}")
    if payload.get("provider") != PROVIDER:
        errors.append(f"provider: expected {PROVIDER}")
    if payload.get("symbol") != SYMBOL:
        errors.append(f"symbol: expected {SYMBOL}")

    date = _date_value(payload.get("date"), "date", errors)
    if date is not None and expected_filename_date is not None:
        if date.strftime("%Y-%m-%d") != expected_filename_date:
            errors.append(
                f"date: payload {date.strftime('%Y-%m-%d')} does not match filename {expected_filename_date}"
            )

    generated = _aware_timestamp(payload.get("generated_at"), "generated_at", errors)
    stored_anchor = _aware_timestamp(payload.get("session_anchor"), "session_anchor", errors)

    if date is not None:
        expected_anchor = pd.Timestamp(_anchor(date))
        if stored_anchor is not None and stored_anchor != expected_anchor:
            errors.append(
                f"session_anchor: expected {expected_anchor.isoformat()}, got {stored_anchor.isoformat()}"
            )
        active = bool(date >= FORWARD_START)
        if bool(payload.get("active_after_registration")) != active:
            errors.append("active_after_registration: inconsistent with forward_start/date")
        if payload.get("forward_start") != FORWARD_START.strftime("%Y-%m-%d"):
            errors.append("forward_start: inconsistent with frozen registration")

        if generated is not None:
            precommitted = bool(generated < expected_anchor)
            expected_eligible = bool(active and precommitted)
            if bool(payload.get("precommitted_before_anchor")) != precommitted:
                errors.append("precommitted_before_anchor: inconsistent with generated_at/session_anchor")
            if bool(payload.get("confirmatory_eligible")) != expected_eligible:
                errors.append("confirmatory_eligible: inconsistent with independently recomputed eligibility")

        train_last = _date_value(payload.get("training_last_market_date"), "training_last_market_date", errors)
        if train_last is not None and train_last >= date:
            errors.append("training_last_market_date: must be strictly before target date")

        manifest = payload.get("market_manifest")
        if manifest is not None:
            if not isinstance(manifest, dict):
                errors.append("market_manifest: must be an object or null")
            else:
                manifest_last = _date_value(manifest.get("last_date"), "market_manifest.last_date", errors)
                if manifest_last is not None and manifest_last >= date:
                    errors.append("market_manifest.last_date: must be strictly before target date")
                if train_last is not None and manifest_last is not None and train_last > manifest_last:
                    errors.append("training_last_market_date: cannot exceed market_manifest.last_date")
                requested_end = manifest.get("requested_end")
                if requested_end:
                    try:
                        req_end = pd.Timestamp(datetime.strptime(str(requested_end), "%Y%m%d")).normalize()
                        if req_end >= date:
                            errors.append("market_manifest.requested_end: must be strictly before target date")
                    except Exception:
                        errors.append("market_manifest.requested_end: expected YYYYMMDD")

    if payload.get("calendar_status") != "candidate_session_unconfirmed":
        errors.append("calendar_status: unexpected value")

    candidates = payload.get("candidate_branches")
    if candidates != list(CANDIDATES):
        errors.append(f"candidate_branches: expected frozen ordered family {list(CANDIDATES)}")
    controls = payload.get("negative_controls")
    if controls != list(NEGATIVE_CONTROLS):
        errors.append(f"negative_controls: expected frozen ordered controls {list(NEGATIVE_CONTROLS)}")

    expected_models = {"baseline", *ALL_BRANCHES}
    predictions = payload.get("predictions")
    if not isinstance(predictions, dict):
        errors.append("predictions: must be an object")
        predictions = {}
    if set(predictions) != expected_models:
        errors.append(f"predictions: model set mismatch; expected {sorted(expected_models)}")

    labels = payload.get("forecast_labels")
    if not isinstance(labels, dict):
        errors.append("forecast_labels: must be an object")
        labels = {}
    if set(labels) != expected_models:
        errors.append(f"forecast_labels: model set mismatch; expected {sorted(expected_models)}")

    for model in expected_models:
        item = predictions.get(model)
        if not isinstance(item, dict):
            continue
        try:
            prob = float(item.get("prob_up"))
        except Exception:
            errors.append(f"predictions.{model}.prob_up: not numeric")
            continue
        if not np.isfinite(prob) or not (0.0 <= prob <= 1.0):
            errors.append(f"predictions.{model}.prob_up: must be finite in [0,1]")
        try:
            best_c = float(item.get("best_C"))
        except Exception:
            errors.append(f"predictions.{model}.best_C: not numeric")
        else:
            if best_c not in ALLOWED_C:
                errors.append(f"predictions.{model}.best_C: outside frozen C grid")
        if model in labels:
            expected_label = "up" if prob >= 0.5 else "down"
            if labels[model] != expected_label:
                errors.append(f"forecast_labels.{model}: inconsistent with prob_up")

    states = payload.get("branch_states")
    if not isinstance(states, dict):
        errors.append("branch_states: must be an object")
        states = {}
    if set(states) != set(ALL_BRANCHES):
        errors.append(f"branch_states: branch set mismatch; expected {sorted(ALL_BRANCHES)}")
    for branch in ALL_BRANCHES:
        state = states.get(branch)
        if not isinstance(state, dict):
            continue
        expected_features = set(_features_for_branch(branch))
        if set(state) != expected_features:
            errors.append(f"branch_states.{branch}: feature set mismatch")

    code_commit = str(payload.get("code_commit", ""))
    if not _SHA40.fullmatch(code_commit):
        errors.append("code_commit: expected a 40-character lowercase git SHA")

    try:
        training_rows = int(payload.get("training_rows"))
        if training_rows <= 0:
            errors.append("training_rows: must be positive")
    except Exception:
        errors.append("training_rows: must be a positive integer")

    return errors


def _repo_relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _git_touch_history(path: Path, repo_root: Path) -> list[tuple[str, pd.Timestamp]]:
    rel = _repo_relative(path, repo_root)
    proc = subprocess.run(
        ["git", "log", "--follow", "--format=%H%x09%cI", "--", rel],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git log failed for {rel}")
    rows: list[tuple[str, pd.Timestamp]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        sha, stamp = line.split("\t", 1)
        rows.append((sha, pd.Timestamp(stamp)))
    return rows


def audit_git_immutability(path: Path, payload: dict[str, Any], repo_root: Path) -> list[str]:
    """Require a committed record to have exactly one touch in reachable git history."""
    errors: list[str] = []
    try:
        touches = _git_touch_history(path, repo_root)
    except Exception as exc:
        return [f"git_history: {exc}"]

    if len(touches) != 1:
        errors.append(f"git_history: prediction file must have exactly one commit touch, got {len(touches)}")
        return errors

    _, commit_time = touches[0]
    date = _date_value(payload.get("date"), "date", errors)
    if date is not None:
        anchor = pd.Timestamp(_anchor(date))
        if commit_time.tzinfo is None:
            errors.append("git_history: commit time is not timezone-aware")
        elif commit_time >= anchor:
            errors.append(
                f"git_history: first/only commit {commit_time.isoformat()} is not before anchor {anchor.isoformat()}"
            )

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

    return errors


def audit_meta_directory(
    predictions_dir: Path,
    *,
    repo_root: Path | None = None,
    verify_git_history: bool = True,
) -> dict[str, Any]:
    failures: dict[str, list[str]] = {}
    records = 0
    independently_eligible = 0
    seen_dates: set[str] = set()

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
                errors.extend(audit_git_immutability(path, payload, repo_root))

        if errors:
            failures[path.name] = sorted(set(errors))

    return {
        "schema_version": 1,
        "family_id": FAMILY_ID,
        "records": records,
        "independently_eligible_records": independently_eligible,
        "git_history_verified": bool(verify_git_history),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "note": "Git committer time is an audit signal, not an external trusted timestamp authority.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit immutable META_FWD_001 prediction records")
    parser.add_argument("--predictions-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--skip-git-history", action="store_true")
    args = parser.parse_args()

    result = audit_meta_directory(
        args.predictions_dir,
        repo_root=args.repo_root,
        verify_git_history=not args.skip_git_history,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
