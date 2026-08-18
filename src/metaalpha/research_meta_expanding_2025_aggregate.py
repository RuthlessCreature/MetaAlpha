from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

from .hybrid_model import (
    block_bootstrap_mean_improvement_probability,
    evaluate_probabilities,
    rowwise_brier,
    rowwise_log_loss,
)
from .meta_branch import META_CANDIDATE_FEATURES, META_NEGATIVE_CONTROL_FEATURES


HYPOTHESIS_ID = "META_HIST_EXPANDING_2025_001"
CANDIDATES = tuple(META_CANDIDATE_FEATURES)
NEGATIVE_CONTROLS = tuple(META_NEGATIVE_CONTROL_FEATURES)
MODELS = ("baseline", *CANDIDATES, *NEGATIVE_CONTROLS)
BOOTSTRAP_BLOCK = 20
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 20260818


def _load_workers(input_dir: Path) -> pd.DataFrame:
    """Load either one file per model or multiple contiguous chunk files per model."""
    parts: dict[str, pd.DataFrame] = {}
    for model in MODELS:
        paths = sorted(input_dir.glob(f"{model}*.csv"))
        paths = [p for p in paths if not p.name.startswith("manifest_")]
        if not paths:
            raise FileNotFoundError(input_dir / f"{model}*.csv")
        frames = [pd.read_csv(path) for path in paths]
        frame = pd.concat(frames, ignore_index=True)
        if set(frame["model_id"].unique()) != {model}:
            raise ValueError(f"worker files for {model} have wrong model_id")
        frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
        if frame["date"].duplicated().any():
            dup = frame.loc[frame["date"].duplicated(), "date"].dt.strftime("%Y-%m-%d").tolist()
            raise ValueError(f"duplicate dates for {model}: {dup[:5]}")
        parts[model] = frame.sort_values("date").reset_index(drop=True)

    ref = parts["baseline"][["date", "target", "same_session_return"]].copy()
    out = ref.copy()
    for model, frame in parts.items():
        check = ref.merge(
            frame[["date", "target", "same_session_return"]],
            on="date",
            how="outer",
            suffixes=("_ref", "_model"),
            indicator=True,
        )
        if not (check["_merge"] == "both").all():
            raise ValueError(f"date coverage mismatch for {model}")
        if not (check["target_ref"].astype(int) == check["target_model"].astype(int)).all():
            raise ValueError(f"target mismatch for {model}")
        if not np.allclose(check["same_session_return_ref"], check["same_session_return_model"], rtol=0, atol=1e-15):
            raise ValueError(f"return mismatch for {model}")
        out = out.merge(
            frame[["date", "prob_up", "best_C", "training_rows", "training_last_date"]].rename(
                columns={
                    "prob_up": f"{model}_prob",
                    "best_C": f"{model}_C",
                    "training_rows": f"{model}_training_rows",
                    "training_last_date": f"{model}_training_last_date",
                }
            ),
            on="date",
            how="inner",
            validate="one_to_one",
        )
    return out.sort_values("date").reset_index(drop=True)


def _metrics_for(df: pd.DataFrame, slice_id: str) -> list[dict[str, object]]:
    if df.empty:
        return []
    y = df["target"].astype(int).to_numpy()
    r = df["same_session_return"].astype(float).to_numpy()
    rows: list[dict[str, object]] = []
    for model in MODELS:
        m = evaluate_probabilities(y, df[f"{model}_prob"].to_numpy(float), r)
        row = asdict(m)
        row.update({"slice": slice_id, "model_id": model})
        rows.append(row)
    return rows


def _slice_metrics(pred: pd.DataFrame) -> pd.DataFrame:
    rows = _metrics_for(pred, "full")
    years = pred["date"].dt.year
    for year in sorted(years.unique()):
        rows.extend(_metrics_for(pred.loc[years == year], f"year_{year}"))
    months = pred["date"].dt.to_period("M")
    for month in sorted(months.unique()):
        rows.extend(_metrics_for(pred.loc[months == month], f"month_{month}"))
    return pd.DataFrame(rows)


def _comparison(pred: pd.DataFrame) -> pd.DataFrame:
    y = pred["target"].astype(int).to_numpy()
    r = pred["same_session_return"].astype(float).to_numpy()
    base_p = pred["baseline_prob"].to_numpy(float)
    base_m = evaluate_probabilities(y, base_p, r)
    base_ll = rowwise_log_loss(y, base_p)
    base_br = rowwise_brier(y, base_p)
    rows: list[dict[str, object]] = []
    for i, model in enumerate((*CANDIDATES, *NEGATIVE_CONTROLS)):
        p = pred[f"{model}_prob"].to_numpy(float)
        m = evaluate_probabilities(y, p, r)
        ll_imp = base_ll - rowwise_log_loss(y, p)
        br_imp = base_br - rowwise_brier(y, p)
        ll_prob, ll_lo, ll_hi = block_bootstrap_mean_improvement_probability(
            ll_imp, block_size=BOOTSTRAP_BLOCK, repetitions=BOOTSTRAP_REPS, seed=BOOTSTRAP_SEED + 2 * i
        )
        br_prob, br_lo, br_hi = block_bootstrap_mean_improvement_probability(
            br_imp, block_size=BOOTSTRAP_BLOCK, repetitions=BOOTSTRAP_REPS, seed=BOOTSTRAP_SEED + 2 * i + 1
        )
        rows.append({
            "model_id": model,
            "negative_control": int(model in NEGATIVE_CONTROLS),
            "logloss_improvement_vs_baseline": float(base_m.log_loss - m.log_loss),
            "brier_improvement_vs_baseline": float(base_m.brier_score - m.brier_score),
            "auc_delta_vs_baseline": float(m.roc_auc - base_m.roc_auc),
            "accuracy_delta_vs_baseline": float(m.accuracy - base_m.accuracy),
            "bootstrap_logloss_probability_positive": ll_prob,
            "bootstrap_logloss_ci025": ll_lo,
            "bootstrap_logloss_ci975": ll_hi,
            "bootstrap_brier_probability_positive": br_prob,
            "bootstrap_brier_ci025": br_lo,
            "bootstrap_brier_ci975": br_hi,
        })
    return pd.DataFrame(rows).sort_values("logloss_improvement_vs_baseline", ascending=False).reset_index(drop=True)


def _advantage_curves(pred: pd.DataFrame) -> pd.DataFrame:
    y = pred["target"].astype(int).to_numpy()
    base_p = pred["baseline_prob"].to_numpy(float)
    base_ll = rowwise_log_loss(y, base_p)
    base_br = rowwise_brier(y, base_p)
    out = pd.DataFrame({"date": pred["date"]})
    for model in (*CANDIDATES, *NEGATIVE_CONTROLS):
        p = pred[f"{model}_prob"].to_numpy(float)
        ll_imp = base_ll - rowwise_log_loss(y, p)
        br_imp = base_br - rowwise_brier(y, p)
        out[f"{model}_cum_logloss_advantage"] = np.cumsum(ll_imp)
        out[f"{model}_cum_brier_advantage"] = np.cumsum(br_imp)
        for w in (20, 60, 120):
            out[f"{model}_roll{w}_logloss_improvement"] = pd.Series(ll_imp).rolling(w).mean().to_numpy()
            out[f"{model}_roll{w}_brier_improvement"] = pd.Series(br_imp).rolling(w).mean().to_numpy()
    return out


def _monthly_leaders(metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    month_ids = sorted(s for s in metrics["slice"].unique() if str(s).startswith("month_"))
    for month in month_ids:
        m = metrics.loc[metrics["slice"] == month].set_index("model_id")
        base_ll = float(m.loc["baseline", "log_loss"])
        gains = {model: base_ll - float(m.loc[model, "log_loss"]) for model in (*CANDIDATES, *NEGATIVE_CONTROLS)}
        best_candidate = max(CANDIDATES, key=lambda x: gains[x])
        control = NEGATIVE_CONTROLS[0]
        rows.append({
            "month": month.replace("month_", ""),
            "best_candidate": best_candidate,
            "best_candidate_logloss_improvement": gains[best_candidate],
            "negative_control_logloss_improvement": gains[control],
            "negative_control_beats_best_candidate": int(gains[control] > gains[best_candidate]),
        })
    return pd.DataFrame(rows)


def _c_frequency(pred: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for model in MODELS:
        counts = pred[f"{model}_C"].value_counts(dropna=False).sort_index()
        for c, n in counts.items():
            rows.append({"model_id": model, "C": c, "sessions": int(n), "fraction": float(n / len(pred))})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate META_HIST_EXPANDING_2025_001 worker outputs")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    pred = _load_workers(args.input_dir)
    metrics = _slice_metrics(pred)
    comparison = _comparison(pred)
    curves = _advantage_curves(pred)
    monthly = _monthly_leaders(metrics)
    c_frequency = _c_frequency(pred)

    args.out.mkdir(parents=True, exist_ok=True)
    pred.to_csv(args.out / "daily_predictions.csv", index=False)
    metrics.to_csv(args.out / "metrics_by_slice.csv", index=False)
    comparison.to_csv(args.out / "comparison_vs_baseline.csv", index=False)
    curves.to_csv(args.out / "advantage_curves.csv", index=False)
    monthly.to_csv(args.out / "monthly_regime_diagnostics.csv", index=False)
    c_frequency.to_csv(args.out / "c_selection_frequency.csv", index=False)

    full = metrics.loc[metrics["slice"] == "full", [
        "model_id", "n", "log_loss", "brier_score", "roc_auc", "accuracy", "calibration_slope", "probability_spread_return"
    ]].sort_values("log_loss")
    years = metrics.loc[metrics["slice"].str.startswith("year_"), [
        "slice", "model_id", "n", "log_loss", "brier_score", "roc_auc", "accuracy"
    ]
    control_wins = int(monthly["negative_control_beats_best_candidate"].sum())

    lines = [
        "# META_HIST_EXPANDING_2025_001 — Exact Daily Expanding Reconstruction",
        "",
        "**Evidence status: RETROSPECTIVE / DESCRIPTIVE ONLY.**",
        "",
        "Each eligible trading day is predicted after re-running the frozen inner-CV C selection on all prior eligible rows, then refitting the selected ridge-logistic model. No test-day outcome enters its own fit.",
        "",
        f"Test sessions: **{len(pred):,}** ({pred['date'].min().date()} .. {pred['date'].max().date()})",
        "",
        "## Full-period metrics",
        "",
        tabulate(full, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Increment versus daily expanding baseline",
        "",
        tabulate(comparison, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Calendar-year slices",
        "",
        tabulate(years, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Negative-control regime diagnostic",
        "",
        f"The hash negative control beat the best traditional candidate in **{control_wins}/{len(monthly)} months** by monthly LogLoss improvement.",
        "",
        "The exact reconstruction is retrospective and cannot alter META_FWD_001.",
        "",
    ]
    (args.out / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    (args.out / "run_metadata.json").write_text(json.dumps({
        "hypothesis_id": HYPOTHESIS_ID,
        "status": "RETROSPECTIVE_DESCRIPTIVE",
        "sessions": int(len(pred)),
        "procedure": "daily expanding refit with frozen inner-CV C selection",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print((args.out / "SUMMARY.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
