from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

from .data_sources import fetch_akshare_index
from .hybrid_model import evaluate_probabilities, make_ridge_logistic_pipeline
from .market_baseline import BASE_CATEGORICAL, BASE_CONTINUOUS, TARGET_DIRECTION, TARGET_RETURN
from .meta_branch import META_CANDIDATE_FEATURES, build_meta_historical_dataset


EXPERIMENT_ID = "META_DENSE_SHIFT_NULL_2025_001"
C_FIXED = 0.01
SHIFTS = tuple(range(5, 253))
BRANCHES = tuple(META_CANDIDATE_FEATURES)


def _fit_predict(train: pd.DataFrame, test: pd.DataFrame, categorical: list[str]) -> np.ndarray:
    pipe = make_ridge_logistic_pipeline(list(BASE_CONTINUOUS), categorical, C=C_FIXED)
    y = train[TARGET_DIRECTION].astype(int).to_numpy()
    cols = list(BASE_CONTINUOUS) + categorical
    pipe.fit(train[cols], y)
    return pipe.predict_proba(test[cols])[:, 1].astype(float)


def run_branch(raw: pd.DataFrame, *, branch: str, test_start: str, test_end: str) -> tuple[pd.DataFrame, dict[str, object]]:
    if branch not in BRANCHES:
        raise ValueError(branch)
    original = build_meta_historical_dataset(raw).copy().reset_index(drop=True)
    max_shift = max(SHIFTS)
    common = original.iloc[max_shift:].copy().reset_index(drop=True)
    start = pd.Timestamp(test_start)
    end = pd.Timestamp(test_end)
    train = common.loc[common["date"] < start].copy().reset_index(drop=True)
    test = common.loc[(common["date"] >= start) & (common["date"] <= end)].copy().reset_index(drop=True)
    if len(train) < 7000 or len(test) < 300:
        raise ValueError("unexpected common train/test coverage")

    y = test[TARGET_DIRECTION].astype(int).to_numpy()
    r = test[TARGET_RETURN].astype(float).to_numpy()
    base_p = _fit_predict(train, test, list(BASE_CATEGORICAL))
    base_m = evaluate_probabilities(y, base_p, r)

    features = list(META_CANDIDATE_FEATURES[branch])
    p_actual = _fit_predict(train, test, list(BASE_CATEGORICAL) + features)
    m_actual = evaluate_probabilities(y, p_actual, r)
    actual_ll = float(base_m.log_loss - m_actual.log_loss)
    actual_br = float(base_m.brier_score - m_actual.brier_score)

    rows: list[dict[str, object]] = []
    for i, shift in enumerate(SHIFTS, start=1):
        shifted = original.copy()
        shifted_cols: list[str] = []
        for feature in features:
            name = f"__dense_shift_{shift}__{feature}"
            shifted[name] = original[feature].shift(shift)
            shifted_cols.append(name)
        shifted = shifted.iloc[max_shift:].copy().reset_index(drop=True)
        tr = shifted.loc[shifted["date"] < start].copy().reset_index(drop=True)
        te = shifted.loc[(shifted["date"] >= start) & (shifted["date"] <= end)].copy().reset_index(drop=True)
        p = _fit_predict(tr, te, list(BASE_CATEGORICAL) + shifted_cols)
        m = evaluate_probabilities(y, p, r)
        rows.append({
            "branch": branch,
            "shift_sessions": shift,
            "log_loss": float(m.log_loss),
            "brier_score": float(m.brier_score),
            "roc_auc": float(m.roc_auc),
            "accuracy": float(m.accuracy),
            "logloss_improvement_vs_baseline": float(base_m.log_loss - m.log_loss),
            "brier_improvement_vs_baseline": float(base_m.brier_score - m.brier_score),
        })
        if i == 1 or i % 25 == 0 or i == len(SHIFTS):
            print(f"[{branch}] {i}/{len(SHIFTS)} shift={shift}", flush=True)

    nulls = pd.DataFrame(rows)
    ll = nulls["logloss_improvement_vs_baseline"].to_numpy(float)
    br = nulls["brier_improvement_vs_baseline"].to_numpy(float)
    summary = {
        "branch": branch,
        "baseline_log_loss": float(base_m.log_loss),
        "baseline_brier_score": float(base_m.brier_score),
        "actual_log_loss": float(m_actual.log_loss),
        "actual_brier_score": float(m_actual.brier_score),
        "actual_logloss_improvement_vs_baseline": actual_ll,
        "actual_brier_improvement_vs_baseline": actual_br,
        "null_count": len(nulls),
        "actual_logloss_percentile_vs_shifts": float(np.mean(ll <= actual_ll)),
        "empirical_logloss_p_one_sided": float((1 + np.sum(ll >= actual_ll)) / (len(ll) + 1)),
        "actual_brier_percentile_vs_shifts": float(np.mean(br <= actual_br)),
        "empirical_brier_p_one_sided": float((1 + np.sum(br >= actual_br)) / (len(br) + 1)),
        "null_logloss_mean_improvement": float(ll.mean()),
        "null_logloss_p95_improvement": float(np.quantile(ll, 0.95)),
        "null_brier_mean_improvement": float(br.mean()),
        "null_brier_p95_improvement": float(np.quantile(br, 0.95)),
        "shifts_beating_actual_logloss": int(np.sum(ll > actual_ll)),
        "shifts_beating_or_tying_actual_logloss": int(np.sum(ll >= actual_ll)),
    }
    return nulls, summary


def aggregate(input_dir: Path, out_dir: Path) -> None:
    summaries: list[dict[str, object]] = []
    null_parts: list[pd.DataFrame] = []
    for branch in BRANCHES:
        null_path = input_dir / f"{branch}_nulls.csv"
        summary_path = input_dir / f"{branch}_summary.json"
        if not null_path.exists() or not summary_path.exists():
            raise FileNotFoundError(branch)
        null_parts.append(pd.read_csv(null_path))
        summaries.append(json.loads(summary_path.read_text(encoding="utf-8")))
    summary = pd.DataFrame(summaries).sort_values("actual_logloss_percentile_vs_shifts", ascending=False)
    nulls = pd.concat(null_parts, ignore_index=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "actual_vs_dense_shift_null.csv", index=False)
    nulls.to_csv(out_dir / "dense_shift_results.csv", index=False)
    lines = [
        f"# {EXPERIMENT_ID} — Dense shifted-state matched-null diagnostic",
        "",
        "**RETROSPECTIVE / DESCRIPTIVE ONLY.**",
        "",
        f"Each traditional joint-state path is compared with every integer trading-session shift from 5 through 252 inclusive (**{len(SHIFTS)} nulls per branch**). C is fixed at {C_FIXED} and model capacity is identical.",
        "",
        "## Exact traditional alignment versus dense shifted copies",
        "",
        tabulate(summary, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "Interpretation: the dense family improves empirical p-value resolution. It remains historical specificity evidence only; no result here alters META_FWD_001.",
        "",
    ]
    (out_dir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "run_metadata.json").write_text(json.dumps({
        "experiment_id": EXPERIMENT_ID,
        "status": "RETROSPECTIVE_DESCRIPTIVE",
        "fixed_C": C_FIXED,
        "shift_min": min(SHIFTS),
        "shift_max": max(SHIFTS),
        "nulls_per_branch": len(SHIFTS),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print((out_dir / "SUMMARY.md").read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=EXPERIMENT_ID)
    sub = parser.add_subparsers(dest="command", required=True)
    worker = sub.add_parser("worker")
    worker.add_argument("--branch", required=True, choices=BRANCHES)
    worker.add_argument("--provider", default="sina")
    worker.add_argument("--symbol", default="000001")
    worker.add_argument("--raw-start", default="19901219")
    worker.add_argument("--test-start", default="20250101")
    worker.add_argument("--end", default="20260817")
    worker.add_argument("--out-dir", type=Path, required=True)
    agg = sub.add_parser("aggregate")
    agg.add_argument("--input-dir", type=Path, required=True)
    agg.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "worker":
        raw, _ = fetch_akshare_index(symbol=args.symbol, start_date=args.raw_start, end_date=args.end, provider=args.provider)
        nulls, summary = run_branch(raw, branch=args.branch, test_start=args.test_start, test_end=args.end)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        nulls.to_csv(args.out_dir / f"{args.branch}_nulls.csv", index=False)
        (args.out_dir / f"{args.branch}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        aggregate(args.input_dir, args.out)


if __name__ == "__main__":
    main()
