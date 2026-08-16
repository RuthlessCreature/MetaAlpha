from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from .data_sources import fetch_akshare_index
from .forward_meta import (
    ALL_BRANCHES,
    FAMILY_ID,
    FORWARD_START,
    MIN_GATE_SESSIONS,
    SYMBOL,
    PROVIDER,
    TARGET_DIRECTION,
    TARGET_RETURN,
    _evaluate_branch,
    _json_safe,
    evaluate_gate,
    load_prediction_records,
)


TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")
SETTLEMENT_HOUR = 15
SETTLEMENT_MINUTE = 30
TARGET_ID = "same_session_close_to_close_direction"


def _now_shanghai(value=None) -> pd.Timestamp:
    if value is None:
        value = datetime.now(timezone.utc)
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize(TZ_SHANGHAI)
    else:
        ts = ts.tz_convert(TZ_SHANGHAI)
    return ts


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_payload(manifest) -> dict[str, Any] | None:
    if manifest is None:
        return None
    return json.loads(manifest.to_json())


def _market_with_realized_targets(market: pd.DataFrame) -> pd.DataFrame:
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"], errors="raise").dt.normalize()
    m = m.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    m["previous_market_date"] = m["date"].shift(1)
    m["previous_close"] = m["close"].astype(float).shift(1)
    m[TARGET_RETURN] = m["close"].astype(float) / m["previous_close"] - 1.0
    m[TARGET_DIRECTION] = (m[TARGET_RETURN] > 0.0).astype(float)
    m.loc[m[TARGET_RETURN].isna(), TARGET_DIRECTION] = np.nan
    return m


def _can_settle_target(date: pd.Timestamp, settled_at: pd.Timestamp) -> bool:
    target = pd.Timestamp(date).normalize().tz_localize(TZ_SHANGHAI)
    if settled_at.normalize() > target.normalize():
        return True
    if settled_at.normalize() < target.normalize():
        return False
    cutoff = target.replace(hour=SETTLEMENT_HOUR, minute=SETTLEMENT_MINUTE)
    return bool(settled_at >= cutoff)


def build_realization_payload(
    prediction_path: Path,
    market_row: pd.Series,
    *,
    manifest=None,
    settled_at=None,
) -> dict[str, Any]:
    prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
    date = pd.Timestamp(prediction["date"]).normalize()
    settled = _now_shanghai(settled_at)
    market_date = pd.Timestamp(market_row["date"]).normalize()
    if market_date != date:
        raise ValueError("market row date does not match prediction date")
    if not _can_settle_target(date, settled):
        raise ValueError("refusing to settle target before 15:30 Asia/Shanghai on target date")

    prev_date = pd.Timestamp(market_row["previous_market_date"]).normalize()
    prev_close = float(market_row["previous_close"])
    close = float(market_row["close"])
    realized_return = float(market_row[TARGET_RETURN])
    direction = int(realized_return > 0.0)
    if not np.isfinite(prev_close) or not np.isfinite(close) or not np.isfinite(realized_return):
        raise ValueError("realized market row contains non-finite values")

    return {
        "schema_version": 1,
        "family_id": FAMILY_ID,
        "date": date.strftime("%Y-%m-%d"),
        "target": TARGET_ID,
        "settled_at": settled.isoformat(),
        "provider": PROVIDER,
        "symbol": SYMBOL,
        "previous_market_date": prev_date.strftime("%Y-%m-%d"),
        "previous_close": prev_close,
        "close": close,
        "realized_return": realized_return,
        "realized_direction": direction,
        "prediction_file": prediction_path.as_posix(),
        "prediction_sha256": _sha256_file(prediction_path),
        "market_manifest": _manifest_payload(manifest),
    }


def validate_realization_payload(
    payload: dict[str, Any],
    *,
    expected_filename_date: str | None = None,
    prediction_path: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("schema_version: expected 1")
    if payload.get("family_id") != FAMILY_ID:
        errors.append(f"family_id: expected {FAMILY_ID}")
    if payload.get("target") != TARGET_ID:
        errors.append(f"target: expected {TARGET_ID}")
    if payload.get("provider") != PROVIDER:
        errors.append(f"provider: expected {PROVIDER}")
    if payload.get("symbol") != SYMBOL:
        errors.append(f"symbol: expected {SYMBOL}")

    try:
        date = pd.Timestamp(payload.get("date")).normalize()
    except Exception as exc:
        errors.append(f"date: invalid: {exc}")
        date = None
    if date is not None and expected_filename_date is not None:
        if date.strftime("%Y-%m-%d") != expected_filename_date:
            errors.append("date: payload does not match filename")

    try:
        prev_date = pd.Timestamp(payload.get("previous_market_date")).normalize()
    except Exception as exc:
        errors.append(f"previous_market_date: invalid: {exc}")
        prev_date = None
    if date is not None and prev_date is not None and prev_date >= date:
        errors.append("previous_market_date: must precede target date")

    try:
        settled = pd.Timestamp(payload.get("settled_at"))
        if settled.tzinfo is None:
            errors.append("settled_at: must be timezone-aware")
        elif date is not None and not _can_settle_target(date, settled.tz_convert(TZ_SHANGHAI)):
            errors.append("settled_at: target was settled before allowed cutoff")
    except Exception as exc:
        errors.append(f"settled_at: invalid: {exc}")

    try:
        prev_close = float(payload.get("previous_close"))
        close = float(payload.get("close"))
        realized_return = float(payload.get("realized_return"))
        direction = int(payload.get("realized_direction"))
        expected_return = close / prev_close - 1.0
        if not all(np.isfinite(v) for v in (prev_close, close, realized_return)):
            errors.append("realized values: must be finite")
        if prev_close <= 0 or close <= 0:
            errors.append("close values: must be positive")
        if not np.isclose(realized_return, expected_return, rtol=0.0, atol=1e-12):
            errors.append("realized_return: inconsistent with close/previous_close")
        if direction not in (0, 1) or direction != int(realized_return > 0.0):
            errors.append("realized_direction: inconsistent with realized_return")
    except Exception as exc:
        errors.append(f"realized values: invalid: {exc}")

    if prediction_path is not None:
        if not prediction_path.exists():
            errors.append("prediction_file: referenced prediction does not exist")
        else:
            expected_hash = _sha256_file(prediction_path)
            if payload.get("prediction_sha256") != expected_hash:
                errors.append("prediction_sha256: does not match immutable prediction file")
            try:
                prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
                if prediction.get("date") != payload.get("date"):
                    errors.append("prediction_file: target date mismatch")
            except Exception as exc:
                errors.append(f"prediction_file: invalid JSON: {exc}")

    manifest = payload.get("market_manifest")
    if manifest is not None:
        if not isinstance(manifest, dict):
            errors.append("market_manifest: must be an object or null")
        elif date is not None:
            try:
                manifest_last = pd.Timestamp(manifest.get("last_date")).normalize()
                if manifest_last < date:
                    errors.append("market_manifest.last_date: does not reach realized target date")
            except Exception as exc:
                errors.append(f"market_manifest.last_date: invalid: {exc}")

    return errors


def write_missing_realizations(
    predictions_dir: Path,
    realized_dir: Path,
    market: pd.DataFrame,
    *,
    manifest=None,
    settled_at=None,
) -> list[Path]:
    realized_dir.mkdir(parents=True, exist_ok=True)
    m = _market_with_realized_targets(market)
    lookup = {row["date"]: row for _, row in m.dropna(subset=[TARGET_RETURN]).iterrows()}
    created: list[Path] = []

    for prediction_path in sorted(predictions_dir.glob("*.json")):
        prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
        if prediction.get("family_id") != FAMILY_ID:
            continue
        date = pd.Timestamp(prediction["date"]).normalize()
        out = realized_dir / f"{date.strftime('%Y-%m-%d')}.json"
        if out.exists() or date not in lookup:
            continue
        settled = _now_shanghai(settled_at)
        if not _can_settle_target(date, settled):
            continue
        payload = build_realization_payload(
            prediction_path,
            lookup[date],
            manifest=manifest,
            settled_at=settled,
        )
        errors = validate_realization_payload(
            payload,
            expected_filename_date=out.stem,
            prediction_path=prediction_path,
        )
        if errors:
            raise ValueError("invalid realization payload: " + "; ".join(errors))
        out.write_text(json.dumps(_json_safe(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        created.append(out)
    return created


def load_realized_records(realized_dir: Path, predictions_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for path in sorted(realized_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("family_id") != FAMILY_ID:
            continue
        prediction_path = predictions_dir / f"{payload['date']}.json"
        errors = validate_realization_payload(
            payload,
            expected_filename_date=path.stem,
            prediction_path=prediction_path,
        )
        if errors:
            raise ValueError(f"invalid locked realization {path}: {'; '.join(errors)}")
        rows.append({
            "date": payload["date"],
            TARGET_RETURN: float(payload["realized_return"]),
            TARGET_DIRECTION: int(payload["realized_direction"]),
            "realization_file": str(path),
        })
    if not rows:
        return pd.DataFrame(columns=["date", TARGET_RETURN, TARGET_DIRECTION, "realization_file"])
    out = pd.DataFrame(rows)
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.normalize()
    if out["date"].duplicated().any():
        raise ValueError("duplicate date in locked realization ledger")
    return out.sort_values("date").reset_index(drop=True)


def _coverage_meta(market: pd.DataFrame, predictions: pd.DataFrame, settled: pd.DataFrame) -> dict[str, Any]:
    eligible = predictions.loc[predictions["confirmatory_eligible"].astype(bool)].copy()
    if settled.empty:
        return {
            "eligible_records": int(len(eligible)),
            "settled_sessions": 0,
            "market_sessions_in_scored_span": 0,
            "market_coverage": 0.0,
        }
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"], errors="raise").dt.normalize()
    start = max(FORWARD_START, settled["date"].min())
    end = settled["date"].max()
    mask = (m["date"] >= start) & (m["date"] <= end)
    market_dates = set(m.loc[mask, "date"])
    expected = len(market_dates)
    eligible_dates = set(eligible.loc[(eligible["date"] >= start) & (eligible["date"] <= end), "date"])
    covered = len(eligible_dates & market_dates)
    return {
        "eligible_records": int(len(eligible)),
        "settled_sessions": int(len(settled)),
        "market_sessions_in_scored_span": int(expected),
        "market_coverage": float(covered / expected) if expected else 0.0,
    }


def score_from_locked_ledger(
    market: pd.DataFrame,
    predictions: pd.DataFrame,
    realized: pd.DataFrame,
    out_dir: Path,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    eligible = predictions.loc[predictions["confirmatory_eligible"].astype(bool)].copy()
    settled = eligible.merge(realized, on="date", how="inner", validate="one_to_one")
    settled = settled.sort_values("date").reset_index(drop=True)
    settled.to_csv(out_dir / "settled_predictions.csv", index=False)

    coverage = _coverage_meta(market, predictions, settled)
    latest: dict[str, Any] = {
        "schema_version": 2,
        "family_id": FAMILY_ID,
        "outcome_source": "immutable_realization_ledger",
        "status": "COLLECTING" if len(settled) < MIN_GATE_SESSIONS else "GATE_ELIGIBLE_OR_LOCKED",
        **coverage,
    }
    if len(settled) >= 20:
        latest["descriptive_branches"] = {b: _evaluate_branch(settled, b) for b in ALL_BRANCHES}

    gate_path = out_dir / "gate_result.json"
    if gate_path.exists():
        latest["gate_locked"] = True
        latest["gate_file"] = str(gate_path)
    elif len(settled) >= MIN_GATE_SESSIONS:
        gate = evaluate_gate(
            settled.iloc[:MIN_GATE_SESSIONS].copy(),
            coverage=float(coverage["market_coverage"]),
        )
        gate["outcome_source"] = "immutable_realization_ledger"
        gate_path.write_text(json.dumps(_json_safe(gate), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        latest["gate_locked"] = True
        latest["gate_created_now"] = True
        latest["winner"] = gate["winner"]
        latest["negative_control_alarm"] = gate["negative_control_alarm"]
    else:
        latest["gate_locked"] = False
        latest["sessions_until_gate"] = MIN_GATE_SESSIONS - len(settled)

    (out_dir / "latest_status.json").write_text(json.dumps(_json_safe(latest), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return latest


def settle_and_score(
    predictions_dir: Path,
    realized_dir: Path,
    out_dir: Path,
    *,
    end: str,
    settled_at=None,
) -> dict[str, Any]:
    market, manifest = fetch_akshare_index(
        symbol=SYMBOL,
        start_date="20260801",
        end_date=end,
        provider=PROVIDER,
    )
    created = write_missing_realizations(
        predictions_dir,
        realized_dir,
        market,
        manifest=manifest,
        settled_at=settled_at,
    )
    predictions = load_prediction_records(predictions_dir)
    realized = load_realized_records(realized_dir, predictions_dir)
    latest = score_from_locked_ledger(market, predictions, realized, out_dir)
    latest["realizations_created_now"] = [p.name for p in created]
    (out_dir / "latest_status.json").write_text(json.dumps(_json_safe(latest), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "scoring_data_manifest.json").write_text(manifest.to_json(), encoding="utf-8")
    return latest


def main() -> None:
    parser = argparse.ArgumentParser(description="Immutable realization ledger for META_FWD_001")
    parser.add_argument("--predictions-dir", type=Path, required=True)
    parser.add_argument("--realized-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--end", required=True)
    args = parser.parse_args()

    latest = settle_and_score(
        args.predictions_dir,
        args.realized_dir,
        args.out_dir,
        end=args.end,
    )
    print(json.dumps(_json_safe(latest), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
