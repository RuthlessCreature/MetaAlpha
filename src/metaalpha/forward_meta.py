from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from .data_sources import fetch_akshare_index
from .hybrid_model import (
    block_bootstrap_mean_improvement_probability,
    evaluate_probabilities,
    fit_predict_probability,
    holm_adjust,
    rowwise_brier,
    rowwise_log_loss,
)
from .market_baseline import BASE_CATEGORICAL, BASE_CONTINUOUS, TARGET_DIRECTION, TARGET_RETURN
from .meta_branch import (
    META_CANDIDATE_FEATURES,
    META_NEGATIVE_CONTROL_FEATURES,
    build_meta_historical_dataset,
    premarket_meta_feature_row,
)


TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")
FAMILY_ID = "META_FWD_001"
VERSION = 1
FORWARD_START = pd.Timestamp("2026-08-17")
ANCHOR_HOUR = 9
ANCHOR_MINUTE = 25
PROVIDER = "sina"
SYMBOL = "000001"
CANDIDATES = tuple(META_CANDIDATE_FEATURES)
NEGATIVE_CONTROLS = tuple(META_NEGATIVE_CONTROL_FEATURES)
ALL_BRANCHES = CANDIDATES + NEGATIVE_CONTROLS
MIN_GATE_SESSIONS = 500
MIN_COVERAGE = 0.98
BOOTSTRAP_BLOCK = 20
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 20260816


def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _shanghai_now(value=None) -> datetime:
    if value is None:
        value = datetime.now(timezone.utc)
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize(TZ_SHANGHAI)
    else:
        ts = ts.tz_convert(TZ_SHANGHAI)
    return ts.to_pydatetime()


def _anchor(date_value) -> datetime:
    d = pd.Timestamp(date_value).date()
    return datetime(d.year, d.month, d.day, ANCHOR_HOUR, ANCHOR_MINUTE, tzinfo=TZ_SHANGHAI)


def _git_sha() -> str:
    env = os.getenv("GITHUB_SHA")
    if env:
        return env
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _features_for_branch(branch_id: str) -> list[str]:
    if branch_id in META_CANDIDATE_FEATURES:
        return META_CANDIDATE_FEATURES[branch_id]
    return META_NEGATIVE_CONTROL_FEATURES[branch_id]


def generate_prediction_record(
    date_value,
    *,
    generated_at=None,
    history: pd.DataFrame | None = None,
    manifest=None,
) -> dict[str, object]:
    date = pd.Timestamp(date_value).normalize()
    generated = _shanghai_now(generated_at)
    anchor = _anchor(date)
    active = date >= FORWARD_START
    precommitted = generated < anchor

    if history is None:
        end = (date - pd.Timedelta(days=1)).strftime("%Y%m%d")
        history, manifest = fetch_akshare_index(
            symbol=SYMBOL,
            start_date="19901219",
            end_date=end,
            provider=PROVIDER,
        )
    history = history.copy()
    history["date"] = pd.to_datetime(history["date"], errors="raise").dt.normalize()
    history = history.loc[history["date"] < date].sort_values("date").reset_index(drop=True)
    if history.empty:
        raise ValueError("no realized market history before target date")

    train = build_meta_historical_dataset(history)
    test = premarket_meta_feature_row(history, date)

    predictions: dict[str, object] = {}
    base_p, base_c, _ = fit_predict_probability(
        train,
        test,
        numeric_cols=list(BASE_CONTINUOUS),
        categorical_cols=list(BASE_CATEGORICAL),
        target_col=TARGET_DIRECTION,
    )
    predictions["baseline"] = {"prob_up": float(base_p[0]), "best_C": float(base_c)}

    states: dict[str, object] = {}
    for branch_id in ALL_BRANCHES:
        features = _features_for_branch(branch_id)
        p, best_c, _ = fit_predict_probability(
            train,
            test,
            numeric_cols=list(BASE_CONTINUOUS),
            categorical_cols=list(BASE_CATEGORICAL) + features,
            target_col=TARGET_DIRECTION,
        )
        predictions[branch_id] = {"prob_up": float(p[0]), "best_C": float(best_c)}
        states[branch_id] = {feature: _json_safe(test.iloc[0][feature]) for feature in features}

    manifest_payload = json.loads(manifest.to_json()) if manifest is not None else None
    return {
        "schema_version": 1,
        "family_id": FAMILY_ID,
        "version": VERSION,
        "date": date.strftime("%Y-%m-%d"),
        "generated_at": generated.isoformat(),
        "session_anchor": anchor.isoformat(),
        "forward_start": FORWARD_START.strftime("%Y-%m-%d"),
        "active_after_registration": bool(active),
        "precommitted_before_anchor": bool(precommitted),
        "confirmatory_eligible": bool(active and precommitted),
        "calendar_status": "candidate_session_unconfirmed",
        "provider": PROVIDER,
        "symbol": SYMBOL,
        "training_last_market_date": train["date"].iloc[-1].strftime("%Y-%m-%d"),
        "training_rows": int(len(train)),
        "code_commit": _git_sha(),
        "market_manifest": manifest_payload,
        "predictions": predictions,
        "branch_states": states,
        "forecast_labels": {
            model: "up" if float(payload["prob_up"]) >= 0.5 else "down"
            for model, payload in predictions.items()
        },
        "candidate_branches": list(CANDIDATES),
        "negative_controls": list(NEGATIVE_CONTROLS),
    }


def write_prediction_record(date_value, out_path: Path, *, generated_at=None) -> dict[str, object]:
    if out_path.exists():
        raise FileExistsError(f"refusing to overwrite precommitted prediction: {out_path}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    record = generate_prediction_record(date_value, generated_at=generated_at)
    out_path.write_text(json.dumps(_json_safe(record), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def load_prediction_records(predictions_dir: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(predictions_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("family_id") != FAMILY_ID:
            continue
        pred = payload["predictions"]
        row = {
            "date": payload["date"],
            "confirmatory_eligible": payload.get("confirmatory_eligible", False),
            "generated_at": payload.get("generated_at"),
            "baseline_prob": pred["baseline"]["prob_up"],
            "source_file": str(path),
        }
        for branch in ALL_BRANCHES:
            row[f"{branch}_prob"] = pred[branch]["prob_up"]
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.normalize()
    return out.sort_values("date").drop_duplicates("date", keep="first").reset_index(drop=True)


def _settle(market: pd.DataFrame, records: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    if records.empty:
        return pd.DataFrame(), {"eligible_records": 0, "market_coverage": 0.0}
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"], errors="raise").dt.normalize()
    m = m.sort_values("date").reset_index(drop=True)
    m[TARGET_RETURN] = m["close"].astype(float).pct_change()
    m[TARGET_DIRECTION] = (m[TARGET_RETURN] > 0.0).astype(int)
    m.loc[m[TARGET_RETURN].isna(), TARGET_DIRECTION] = np.nan

    eligible = records.loc[records["confirmatory_eligible"].astype(bool)].copy()
    joined = eligible.merge(
        m[["date", TARGET_RETURN, TARGET_DIRECTION]], on="date", how="inner", validate="one_to_one"
    ).dropna(subset=[TARGET_RETURN, TARGET_DIRECTION])
    joined[TARGET_DIRECTION] = joined[TARGET_DIRECTION].astype(int)
    joined = joined.sort_values("date").reset_index(drop=True)

    if joined.empty:
        coverage = 0.0
        market_sessions = 0
    else:
        start = max(FORWARD_START, joined["date"].min())
        end = joined["date"].max()
        market_mask = (m["date"] >= start) & (m["date"] <= end)
        market_sessions = int(market_mask.sum())
        eligible_market = eligible.loc[(eligible["date"] >= start) & (eligible["date"] <= end)]
        eligible_market = eligible_market.loc[eligible_market["date"].isin(m.loc[market_mask, "date"])]
        coverage = float(len(eligible_market) / market_sessions) if market_sessions else 0.0
    return joined, {
        "eligible_records": int(len(eligible)),
        "settled_sessions": int(len(joined)),
        "market_sessions_in_scored_span": market_sessions,
        "market_coverage": coverage,
    }


def _evaluate_branch(df: pd.DataFrame, branch_id: str) -> dict[str, object]:
    y = df[TARGET_DIRECTION].to_numpy(int)
    returns = df[TARGET_RETURN].to_numpy(float)
    base = df["baseline_prob"].to_numpy(float)
    aug = df[f"{branch_id}_prob"].to_numpy(float)
    b = evaluate_probabilities(y, base, returns)
    a = evaluate_probabilities(y, aug, returns)
    ll_imp = rowwise_log_loss(y, base) - rowwise_log_loss(y, aug)
    br_imp = rowwise_brier(y, base) - rowwise_brier(y, aug)
    ll_prob, ll_lo, ll_hi = block_bootstrap_mean_improvement_probability(
        ll_imp, block_size=BOOTSTRAP_BLOCK, repetitions=BOOTSTRAP_REPS, seed=BOOTSTRAP_SEED
    )
    br_prob, br_lo, br_hi = block_bootstrap_mean_improvement_probability(
        br_imp, block_size=BOOTSTRAP_BLOCK, repetitions=BOOTSTRAP_REPS, seed=BOOTSTRAP_SEED + 1
    )
    pieces = np.array_split(np.arange(len(df)), 4)
    return {
        "logloss": float(a.log_loss),
        "logloss_improvement": float(b.log_loss - a.log_loss),
        "brier_improvement": float(b.brier_score - a.brier_score),
        "auc_delta": float(a.roc_auc - b.roc_auc),
        "accuracy_delta": float(a.accuracy - b.accuracy),
        "windows_logloss_improved": int(sum(float(ll_imp[idx].mean()) > 0 for idx in pieces)),
        "windows_brier_improved": int(sum(float(br_imp[idx].mean()) > 0 for idx in pieces)),
        "bootstrap_logloss_probability_positive": ll_prob,
        "bootstrap_brier_probability_positive": br_prob,
        "bootstrap_logloss_ci025": ll_lo,
        "bootstrap_logloss_ci975": ll_hi,
        "bootstrap_brier_ci025": br_lo,
        "bootstrap_brier_ci975": br_hi,
        "bootstrap_logloss_p_one_sided": 1.0 - ll_prob,
        "bootstrap_brier_p_one_sided": 1.0 - br_prob,
    }


def _core_checks(r: dict[str, object], coverage: float, *, holm_required: bool) -> dict[str, bool]:
    checks = {
        "coverage_met": coverage >= MIN_COVERAGE,
        "logloss_windows_met": int(r["windows_logloss_improved"]) >= 3,
        "brier_windows_met": int(r["windows_brier_improved"]) >= 3,
        "logloss_effect_met": float(r["logloss_improvement"]) >= 0.001,
        "brier_effect_met": float(r["brier_improvement"]) >= 0.0005,
        "auc_floor_met": float(r["auc_delta"]) >= -0.005,
        "bootstrap_logloss_met": float(r["bootstrap_logloss_probability_positive"]) >= 0.95,
        "bootstrap_brier_met": float(r["bootstrap_brier_probability_positive"]) >= 0.95,
    }
    if holm_required:
        checks["holm_logloss_met"] = float(r["bootstrap_logloss_p_holm"]) <= 0.05
        checks["holm_brier_met"] = float(r["bootstrap_brier_p_holm"]) <= 0.05
    return checks


def evaluate_gate(first_500: pd.DataFrame, *, coverage: float) -> dict[str, object]:
    if len(first_500) != MIN_GATE_SESSIONS:
        raise ValueError(f"gate requires exactly {MIN_GATE_SESSIONS} settled sessions")

    results = {branch: _evaluate_branch(first_500, branch) for branch in ALL_BRANCHES}
    holm_ll = holm_adjust({b: float(results[b]["bootstrap_logloss_p_one_sided"]) for b in CANDIDATES})
    holm_br = holm_adjust({b: float(results[b]["bootstrap_brier_p_one_sided"]) for b in CANDIDATES})

    for branch in CANDIDATES:
        r = results[branch]
        r["bootstrap_logloss_p_holm"] = holm_ll[branch]
        r["bootstrap_brier_p_holm"] = holm_br[branch]
        r["checks"] = _core_checks(r, coverage, holm_required=True)
        r["gate_pass"] = bool(all(r["checks"].values()))
        r["decision"] = "PASS" if r["gate_pass"] else "FAIL"

    control_alarm = False
    for branch in NEGATIVE_CONTROLS:
        r = results[branch]
        r["checks_candidate_like_without_holm"] = _core_checks(r, coverage, holm_required=False)
        r["candidate_like_pass"] = bool(all(r["checks_candidate_like_without_holm"].values()))
        control_alarm = control_alarm or bool(r["candidate_like_pass"])

    passed = [b for b in CANDIDATES if results[b]["gate_pass"]]
    winner = min(passed, key=lambda b: float(results[b]["logloss"])) if passed and not control_alarm else None
    return {
        "schema_version": 1,
        "family_id": FAMILY_ID,
        "version": VERSION,
        "verdict_locked": True,
        "sample_sessions": MIN_GATE_SESSIONS,
        "first_date": first_500["date"].iloc[0].strftime("%Y-%m-%d"),
        "last_date": first_500["date"].iloc[-1].strftime("%Y-%m-%d"),
        "coverage": float(coverage),
        "candidate_results": {b: results[b] for b in CANDIDATES},
        "negative_control_results": {b: results[b] for b in NEGATIVE_CONTROLS},
        "negative_control_alarm": bool(control_alarm),
        "winner": winner,
        "winner_rule": "lowest locked-sample LogLoss among full-gate PASS candidates; no winner if negative-control alarm",
    }


def score_forward(market: pd.DataFrame, records: pd.DataFrame, out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    settled, coverage_meta = _settle(market, records)
    settled.to_csv(out_dir / "settled_predictions.csv", index=False)
    latest: dict[str, object] = {
        "schema_version": 1,
        "family_id": FAMILY_ID,
        "status": "COLLECTING" if len(settled) < MIN_GATE_SESSIONS else "GATE_ELIGIBLE_OR_LOCKED",
        **coverage_meta,
    }
    if len(settled) >= 20:
        latest["descriptive_branches"] = {b: _evaluate_branch(settled, b) for b in ALL_BRANCHES}

    gate_path = out_dir / "gate_result.json"
    if gate_path.exists():
        latest["gate_locked"] = True
        latest["gate_file"] = str(gate_path)
    elif len(settled) >= MIN_GATE_SESSIONS:
        gate = evaluate_gate(settled.iloc[:MIN_GATE_SESSIONS].copy(), coverage=float(coverage_meta["market_coverage"]))
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


def main() -> None:
    parser = argparse.ArgumentParser(description="META_FWD_001 future-only branch tournament")
    sub = parser.add_subparsers(dest="command", required=True)
    p_signal = sub.add_parser("signal")
    p_signal.add_argument("--date", required=True)
    p_signal.add_argument("--out", type=Path, required=True)
    p_score = sub.add_parser("score")
    p_score.add_argument("--predictions-dir", type=Path, required=True)
    p_score.add_argument("--out-dir", type=Path, required=True)
    p_score.add_argument("--end", required=True)
    args = parser.parse_args()

    if args.command == "signal":
        record = write_prediction_record(args.date, args.out)
        print(json.dumps(_json_safe(record), ensure_ascii=False, indent=2))
        return

    records = load_prediction_records(args.predictions_dir)
    market, manifest = fetch_akshare_index(
        symbol=SYMBOL,
        start_date="20260801",
        end_date=args.end,
        provider=PROVIDER,
    )
    latest = score_forward(market, records, args.out_dir)
    (args.out_dir / "scoring_data_manifest.json").write_text(manifest.to_json(), encoding="utf-8")
    print(json.dumps(_json_safe(latest), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
