from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

from .data_sources import fetch_akshare_index
from .hybrid_model import evaluate_probabilities, make_ridge_logistic_pipeline
from .liuyao_hash import add_liuyao_hash_features
from .market_baseline import BASE_CATEGORICAL, BASE_CONTINUOUS, TARGET_DIRECTION, TARGET_RETURN
from .meta_branch import build_meta_historical_dataset


EXPERIMENT_ID = "META_HASH_ENSEMBLE_NULL_2025_001"
C_FIXED = 0.01
SEEDS = tuple(range(100))
TEST_START = pd.Timestamp("2025-01-01")
TEST_END = pd.Timestamp("2026-08-17")
LINE_VALUES = (6, 7, 8, 9)


def _base_yang(v: int) -> int:
    return 1 if v in (7, 9) else 0


def _changed_yang(v: int) -> int:
    if v == 6:
        return 1
    if v == 9:
        return 0
    return _base_yang(v)


def _features_for_date(value, seed: int) -> dict[str, object]:
    date = pd.Timestamp(value).normalize().strftime("%Y-%m-%d")
    salt = f"METAALPHA|HASH_ENSEMBLE_NULL_2025_001|seed={seed}"
    digest = hashlib.sha256(f"{salt}|{date}|09:25:00+08:00".encode("utf-8")).digest()
    lines = tuple(LINE_VALUES[b % 4] for b in digest[:6])
    base = tuple(_base_yang(v) for v in lines)
    changed = tuple(_changed_yang(v) for v in lines)
    moving = tuple(i + 1 for i, v in enumerate(lines) if v in (6, 9))
    p = f"hash_seed_{seed:03d}"
    return {
        f"{p}__base_pattern": "".join(str(x) for x in base),
        f"{p}__changed_pattern": "".join(str(x) for x in changed),
        f"{p}__moving_count": len(moving),
        f"{p}__moving_lines_key": "-".join(str(x) for x in moving) if moving else "none",
    }


def _seed_cols(seed: int) -> list[str]:
    p = f"hash_seed_{seed:03d}"
    return [
        f"{p}__base_pattern",
        f"{p}__changed_pattern",
        f"{p}__moving_count",
        f"{p}__moving_lines_key",
    ]


def _fit_predict(train: pd.DataFrame, test: pd.DataFrame, categorical: list[str]) -> np.ndarray:
    pipe = make_ridge_logistic_pipeline(list(BASE_CONTINUOUS), categorical, C=C_FIXED)
    cols = list(BASE_CONTINUOUS) + categorical
    y = train[TARGET_DIRECTION].astype(int).to_numpy()
    pipe.fit(train[cols], y)
    return pipe.predict_proba(test[cols])[:, 1].astype(float)


def run(raw: pd.DataFrame, *, out_dir: Path, manifest=None) -> None:
    dataset = build_meta_historical_dataset(raw).copy().reset_index(drop=True)
    # build_meta_historical_dataset already contains the frozen LIUYAO_HASH_V1 reference.
    train = dataset.loc[dataset["date"] < TEST_START].copy().reset_index(drop=True)
    test = dataset.loc[(dataset["date"] >= TEST_START) & (dataset["date"] <= TEST_END)].copy().reset_index(drop=True)
    if len(train) < 8000 or len(test) < 300:
        raise ValueError("unexpected train/test coverage")

    y = test[TARGET_DIRECTION].astype(int).to_numpy()
    r = test[TARGET_RETURN].astype(float).to_numpy()
    base_p = _fit_predict(train, test, list(BASE_CATEGORICAL))
    base_m = evaluate_probabilities(y, base_p, r)

    ref_cols = [
        "liuyao_hash__v1__base_pattern",
        "liuyao_hash__v1__changed_pattern",
        "liuyao_hash__v1__moving_count",
        "liuyao_hash__v1__moving_lines_key",
    ]
    ref_p = _fit_predict(train, test, list(BASE_CATEGORICAL) + ref_cols)
    ref_m = evaluate_probabilities(y, ref_p, r)
    ref_ll_imp = float(base_m.log_loss - ref_m.log_loss)
    ref_br_imp = float(base_m.brier_score - ref_m.brier_score)

    rows: list[dict[str, object]] = []
    all_dates = dataset["date"].tolist()
    for seed in SEEDS:
        feats = pd.DataFrame([_features_for_date(v, seed) for v in all_dates], index=dataset.index)
        work = pd.concat([dataset, feats], axis=1)
        tr = work.loc[work["date"] < TEST_START].copy().reset_index(drop=True)
        te = work.loc[(work["date"] >= TEST_START) & (work["date"] <= TEST_END)].copy().reset_index(drop=True)
        cols = _seed_cols(seed)
        p = _fit_predict(tr, te, list(BASE_CATEGORICAL) + cols)
        m = evaluate_probabilities(y, p, r)
        rows.append({
            "seed": seed,
            "log_loss": float(m.log_loss),
            "brier_score": float(m.brier_score),
            "roc_auc": float(m.roc_auc),
            "accuracy": float(m.accuracy),
            "logloss_improvement_vs_baseline": float(base_m.log_loss - m.log_loss),
            "brier_improvement_vs_baseline": float(base_m.brier_score - m.brier_score),
        })
        if seed == 0 or (seed + 1) % 10 == 0:
            print(f"hash seed {seed+1}/{len(SEEDS)}", flush=True)

    seeds = pd.DataFrame(rows).sort_values("logloss_improvement_vs_baseline", ascending=False).reset_index(drop=True)
    ll = seeds["logloss_improvement_vs_baseline"].to_numpy(float)
    br = seeds["brier_improvement_vs_baseline"].to_numpy(float)
    summary = pd.DataFrame([{
        "baseline_log_loss": float(base_m.log_loss),
        "baseline_brier_score": float(base_m.brier_score),
        "reference_hash_log_loss": float(ref_m.log_loss),
        "reference_hash_brier_score": float(ref_m.brier_score),
        "reference_hash_logloss_improvement": ref_ll_imp,
        "reference_hash_brier_improvement": ref_br_imp,
        "seed_count": len(seeds),
        "fraction_seed_hashes_beating_baseline_logloss": float(np.mean(ll > 0.0)),
        "fraction_seed_hashes_beating_baseline_brier": float(np.mean(br > 0.0)),
        "mean_seed_logloss_improvement": float(ll.mean()),
        "median_seed_logloss_improvement": float(np.median(ll)),
        "p95_seed_logloss_improvement": float(np.quantile(ll, 0.95)),
        "reference_hash_percentile_vs_100_seeds_logloss": float(np.mean(ll <= ref_ll_imp)),
        "reference_hash_tail_fraction_vs_100_seeds_logloss": float((1 + np.sum(ll >= ref_ll_imp)) / (len(ll) + 1)),
        "mean_seed_brier_improvement": float(br.mean()),
        "median_seed_brier_improvement": float(np.median(br)),
        "p95_seed_brier_improvement": float(np.quantile(br, 0.95)),
        "reference_hash_percentile_vs_100_seeds_brier": float(np.mean(br <= ref_br_imp)),
        "reference_hash_tail_fraction_vs_100_seeds_brier": float((1 + np.sum(br >= ref_br_imp)) / (len(br) + 1)),
    }])

    out_dir.mkdir(parents=True, exist_ok=True)
    seeds.to_csv(out_dir / "hash_seed_results.csv", index=False)
    summary.to_csv(out_dir / "summary_metrics.csv", index=False)
    lines = [
        f"# {EXPERIMENT_ID} — 100-seed hash negative-control ensemble",
        "",
        "**RETROSPECTIVE / NEGATIVE-CONTROL DIAGNOSTIC ONLY.**",
        "",
        f"Train rows: **{len(train):,}**; test rows: **{len(test):,}** ({test['date'].min().date()} .. {test['date'].max().date()}).",
        f"All 100 salts were frozen as seed IDs 0..99. C is fixed at {C_FIXED}. Every seed uses the same four-feature representation as LIUYAO_HASH_V1.",
        "",
        "## Ensemble summary",
        "",
        tabulate(summary, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Top 20 synthetic hashes by LogLoss improvement",
        "",
        tabulate(seeds.head(20), headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "Interpretation: if many seeds beat baseline, generic deterministic date partitioning is sufficient to create apparent signal. If the frozen LIUYAO_HASH_V1 is extreme among seeds, its prior win is consistent with a lucky frozen random encoding. Either way this is a negative control, not a divination claim.",
        "",
    ]
    if manifest is not None:
        lines.extend(["## Data manifest", "", "```json", manifest.to_json(), "```", ""])
    (out_dir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "run_metadata.json").write_text(json.dumps({
        "experiment_id": EXPERIMENT_ID,
        "status": "RETROSPECTIVE_NEGATIVE_CONTROL_DIAGNOSTIC",
        "fixed_C": C_FIXED,
        "seed_ids": list(SEEDS),
        "reference": "LIUYAO_HASH_V1",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print((out_dir / "SUMMARY.md").read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=EXPERIMENT_ID)
    parser.add_argument("--provider", default="sina")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--raw-start", default="19901219")
    parser.add_argument("--end", default="20260817")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw, manifest = fetch_akshare_index(symbol=args.symbol, start_date=args.raw_start, end_date=args.end, provider=args.provider)
    run(raw, out_dir=args.out, manifest=manifest)


if __name__ == "__main__":
    main()
