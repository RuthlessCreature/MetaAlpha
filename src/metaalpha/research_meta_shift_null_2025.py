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


HYPOTHESIS_ID = "META_SHIFT_NULL_2025_001"
C_FIXED = 0.01
SHIFTS = (5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 109, 113, 127, 131, 137, 149, 157, 167, 181, 197, 211, 227, 241)
BRANCHES = tuple(META_CANDIDATE_FEATURES)


def _fit_predict(train: pd.DataFrame, test: pd.DataFrame, categorical: list[str]) -> np.ndarray:
    pipe = make_ridge_logistic_pipeline(list(BASE_CONTINUOUS), categorical, C=C_FIXED)
    y = train[TARGET_DIRECTION].astype(int).to_numpy()
    cols = list(BASE_CONTINUOUS) + categorical
    pipe.fit(train[cols], y)
    return pipe.predict_proba(test[cols])[:, 1].astype(float)


def run(raw: pd.DataFrame, *, test_start: str, test_end: str, out_dir: Path, manifest=None) -> None:
    dataset = build_meta_historical_dataset(raw).copy().reset_index(drop=True)
    max_shift = max(SHIFTS)
    dataset = dataset.iloc[max_shift:].copy().reset_index(drop=True)

    start = pd.Timestamp(test_start)
    end = pd.Timestamp(test_end)
    train = dataset.loc[dataset["date"] < start].copy().reset_index(drop=True)
    test = dataset.loc[(dataset["date"] >= start) & (dataset["date"] <= end)].copy().reset_index(drop=True)
    if len(train) < 7000 or len(test) < 300:
        raise ValueError("unexpected train/test coverage")

    y_test = test[TARGET_DIRECTION].astype(int).to_numpy()
    r_test = test[TARGET_RETURN].astype(float).to_numpy()
    base_p = _fit_predict(train, test, list(BASE_CATEGORICAL))
    base_m = evaluate_probabilities(y_test, base_p, r_test)

    actual_rows: list[dict[str, object]] = []
    null_rows: list[dict[str, object]] = []

    # Build shifts on the original full eligible sequence so each shifted state
    # preserves the branch's joint categorical path; after max_shift trimming all
    # registered shifts are non-missing on train and test.
    original = build_meta_historical_dataset(raw).copy().reset_index(drop=True)

    for branch in BRANCHES:
        features = list(META_CANDIDATE_FEATURES[branch])
        p_actual = _fit_predict(train, test, list(BASE_CATEGORICAL) + features)
        m_actual = evaluate_probabilities(y_test, p_actual, r_test)
        actual_ll_imp = float(base_m.log_loss - m_actual.log_loss)
        actual_br_imp = float(base_m.brier_score - m_actual.brier_score)

        branch_null_ll: list[float] = []
        branch_null_br: list[float] = []
        for shift in SHIFTS:
            shifted = original.copy()
            shifted_cols: list[str] = []
            for feature in features:
                new = f"__shift_{shift}__{feature}"
                shifted[new] = original[feature].shift(shift)
                shifted_cols.append(new)
            shifted = shifted.iloc[max_shift:].copy().reset_index(drop=True)
            tr = shifted.loc[shifted["date"] < start].copy().reset_index(drop=True)
            te = shifted.loc[(shifted["date"] >= start) & (shifted["date"] <= end)].copy().reset_index(drop=True)
            if te[shifted_cols].isna().any().any() or tr[shifted_cols].isna().any().any():
                raise ValueError(f"unexpected shifted missing values branch={branch} shift={shift}")
            p = _fit_predict(tr, te, list(BASE_CATEGORICAL) + shifted_cols)
            m = evaluate_probabilities(y_test, p, r_test)
            ll_imp = float(base_m.log_loss - m.log_loss)
            br_imp = float(base_m.brier_score - m.brier_score)
            branch_null_ll.append(ll_imp)
            branch_null_br.append(br_imp)
            null_rows.append({
                "branch": branch,
                "shift_sessions": shift,
                "log_loss": float(m.log_loss),
                "brier_score": float(m.brier_score),
                "roc_auc": float(m.roc_auc),
                "accuracy": float(m.accuracy),
                "logloss_improvement_vs_baseline": ll_imp,
                "brier_improvement_vs_baseline": br_imp,
            })

        ll_arr = np.asarray(branch_null_ll)
        br_arr = np.asarray(branch_null_br)
        actual_rows.append({
            "branch": branch,
            "actual_log_loss": float(m_actual.log_loss),
            "actual_brier_score": float(m_actual.brier_score),
            "actual_roc_auc": float(m_actual.roc_auc),
            "actual_accuracy": float(m_actual.accuracy),
            "actual_logloss_improvement_vs_baseline": actual_ll_imp,
            "actual_brier_improvement_vs_baseline": actual_br_imp,
            "shift_null_logloss_mean_improvement": float(ll_arr.mean()),
            "shift_null_logloss_p95_improvement": float(np.quantile(ll_arr, 0.95)),
            "actual_logloss_percentile_vs_shifts": float(np.mean(actual_ll_imp > ll_arr)),
            "empirical_logloss_p_one_sided": float((1 + np.sum(ll_arr >= actual_ll_imp)) / (1 + len(ll_arr))),
            "shift_null_brier_mean_improvement": float(br_arr.mean()),
            "shift_null_brier_p95_improvement": float(np.quantile(br_arr, 0.95)),
            "actual_brier_percentile_vs_shifts": float(np.mean(actual_br_imp > br_arr)),
            "empirical_brier_p_one_sided": float((1 + np.sum(br_arr >= actual_br_imp)) / (1 + len(br_arr))),
        })

    actual = pd.DataFrame(actual_rows).sort_values("actual_logloss_improvement_vs_baseline", ascending=False)
    nulls = pd.DataFrame(null_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    actual.to_csv(out_dir / "actual_vs_shift_null.csv", index=False)
    nulls.to_csv(out_dir / "shift_null_results.csv", index=False)

    summary = [
        "# META_SHIFT_NULL_2025_001 — Shifted-State Matched Null Diagnostic",
        "",
        "**Evidence status: RETROSPECTIVE / DESCRIPTIVE ONLY.**",
        "",
        f"Train rows: **{len(train):,}**; test rows: **{len(test):,}** ({test['date'].min().date()} .. {test['date'].max().date()}).",
        f"Model C fixed at **{C_FIXED}** for actual and shifted copies. Each branch is compared with **{len(SHIFTS)}** trading-session shifts of its own joint state sequence.",
        "",
        f"Baseline LogLoss: **{base_m.log_loss:.6f}**; Brier: **{base_m.brier_score:.6f}**.",
        "",
        "## Traditional mapping versus its shifted copies",
        "",
        tabulate(actual, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Interpretation rule",
        "",
        "A branch beating baseline is not sufficient. If its actual date alignment is not near the top of the shifted-state null distribution, the result is compatible with generic temporal partitioning rather than unique information in the traditional mapping.",
        "",
    ]
    if manifest is not None:
        summary.extend(["## Data manifest", "", "```json", manifest.to_json(), "```", ""])
    (out_dir / "SUMMARY.md").write_text("\n".join(summary), encoding="utf-8")
    (out_dir / "run_metadata.json").write_text(json.dumps({
        "hypothesis_id": HYPOTHESIS_ID,
        "status": "RETROSPECTIVE_DESCRIPTIVE",
        "fixed_C": C_FIXED,
        "shift_sessions": list(SHIFTS),
        "branches": list(BRANCHES),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print((out_dir / "SUMMARY.md").read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run META_SHIFT_NULL_2025_001")
    parser.add_argument("--provider", default="sina")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--raw-start", default="19901219")
    parser.add_argument("--test-start", default="20250101")
    parser.add_argument("--end", default="20260817")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw, manifest = fetch_akshare_index(
        symbol=args.symbol,
        start_date=args.raw_start,
        end_date=args.end,
        provider=args.provider,
    )
    run(raw, test_start=args.test_start, test_end=args.end, out_dir=args.out, manifest=manifest)


if __name__ == "__main__":
    main()
