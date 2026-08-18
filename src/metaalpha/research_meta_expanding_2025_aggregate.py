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
    parts: dict[str, pd.DataFrame] = {}
    for model in MODELS:
        path = input_dir / f"{model}.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path)
        if set(frame["model_id"].unique()) != {model}:
            raise ValueError(f"worker file {path} has wrong model_id")
        frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
        if frame["date"].duplicated().any():
            raise ValueError(f"duplicate dates in {path}")
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
    base_ll = rowwise_log_loss(y, pred["baseline_prob"].to_numpy(float))
    base_br = rowwise_brier(y, pred["baseline_prob"].to_numpy(float))
    out = pred[["date", "target", "same_session_return"]].copy()
    for model in (*CANDIDATES, *NEGATIVE_CONTROLS):
        ll_imp = base_ll - rowwise_log_loss(y, pred[f"{model}_prob"].to_numpy(float))
        br_imp = base_br - rowwise_brier(y, pred[f"{model}_prob"].to_numpy(float))
        s_ll = pd.Series(ll_imp)
        s_br = pd.Series(br_imp)
        out[f"{model}_cum_logloss_advantage"] = s_ll.cumsum().to_numpy()
        out[f"{model}_cum_brier_advantage"] = s_br.cumsum().to_numpy()
        for window in (20, 60, 120):
            out[f"{model}_roll{window}_logloss_improvement"] = s_ll.rolling(window, min_periods=window).mean().to_numpy()
            out[f"{model}_roll{window}_brier_improvement"] = s_br.rolling(window, min_periods=window).mean().to_numpy()
    return out


def _monthly_leaders(metrics: pd.DataFrame) -> pd.DataFrame:
    months = metrics.loc[metrics["slice"].str.startswith("month_")].copy()
    rows: list[dict[str, object]] = []
    for slice_id, group in months.groupby("slice", sort=True):
        by_model = group.set_index("model_id")
        base_ll = float(by_model.loc["baseline", "log_loss"])
        improvements = {m: base_ll - float(by_model.loc[m, "log_loss"]) for m in (*CANDIDATES, *NEGATIVE_CONTROLS)}
        candidate_leader = max(CANDIDATES, key=lambda m: improvements[m])
        all_leader = max((*CANDIDATES, *NEGATIVE_CONTROLS), key=lambda m: improvements[m])
        control = NEGATIVE_CONTROLS[0]
        rows.append({
            "month": slice_id.removeprefix("month_"),
            "candidate_leader": candidate_leader,
            "candidate_leader_logloss_improvement": improvements[candidate_leader],
            "all_leader": all_leader,
            "all_leader_logloss_improvement": improvements[all_leader],
            "negative_control_logloss_improvement": improvements[control],
            "negative_control_beats_best_candidate": int(improvements[control] > improvements[candidate_leader]),
            **{f"{m}_logloss_improvement": improvements[m] for m in (*CANDIDATES, *NEGATIVE_CONTROLS)},
        })
    return pd.DataFrame(rows)


def _c_frequency(pred: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for model in MODELS:
        counts = pred[f"{model}_C"].value_counts(dropna=False).sort_index()
        for c, n in counts.items():
            rows.append({"model_id": model, "C": c, "sessions": int(n), "fraction": float(n / len(pred))})
    return pd.DataFrame(rows)


def _summary(
    pred: pd.DataFrame,
    metrics: pd.DataFrame,
    comparison: pd.DataFrame,
    monthly: pd.DataFrame,
    c_frequency: pd.DataFrame,
    manifest_text: str | None,
) -> str:
    full = metrics.loc[metrics["slice"] == "full", [
        "model_id", "n", "log_loss", "brier_score", "roc_auc", "accuracy", "calibration_slope", "probability_spread_return"
    ]].sort_values("log_loss")
    years = metrics.loc[metrics["slice"].str.startswith("year_"), [
        "slice", "model_id", "n", "log_loss", "brier_score", "roc_auc", "accuracy"
    ]
    control_month_wins = int(monthly["negative_control_beats_best_candidate"].sum())
    month_n = int(len(monthly))
    latest_curve = _advantage_curves(pred).iloc[-1]
    latest_roll_rows = []
    for model in (*CANDIDATES, *NEGATIVE_CONTROLS):
        latest_roll_rows.append({
            "model_id": model,
            "cum_logloss_advantage": float(latest_curve[f"{model}_cum_logloss_advantage"]),
            "roll20_ll_improvement": latest_curve[f"{model}_roll20_logloss_improvement"],
            "roll60_ll_improvement": latest_curve[f"{model}_roll60_logloss_improvement"],
            "roll120_ll_improvement": latest_curve[f"{model}_roll120_logloss_improvement"],
        })
    latest_roll = pd.DataFrame(latest_roll_rows).sort_values("cum_logloss_advantage", ascending=False)

    lines = [
        "# META_HIST_EXPANDING_2025_001 — Daily Expanding Reconstruction",
        "",
        "**Evidence status: RETROSPECTIVE / DESCRIPTIVE ONLY.** Every test-day model is tuned and fitted using only prior eligible trading days, but the candidate family itself was designed after these outcomes existed. This experiment cannot alter `META_FWD_001`.",
        "",
        f"Test sessions: **{len(pred):,}** ({pred['date'].min().date()} .. {pred['date'].max().date()})",
        "Procedure: daily expanding refit; frozen C grid and inner-CV rule; same frozen baseline and symbolic feature blocks as META_FWD_001.",
        "",
        "## Full-period metrics",
        "",
        tabulate(full, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Increment versus identical daily baseline",
        "",
        tabulate(comparison, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Calendar-year slices",
        "",
        tabulate(years, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Latest cumulative / rolling information advantage",
        "",
        tabulate(latest_roll, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Regime warning",
        "",
        f"The deterministic hash negative control beat the best traditional candidate in **{control_month_wins}/{month_n} calendar months** on monthly LogLoss improvement.",
        "This count is diagnostic, not a p-value. Frequent control dominance argues that date-state partitioning / regime coincidence may explain apparent branch wins.",
        "",
        "## C selection frequency",
        "",
        tabulate(c_frequency, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Framework implication",
        "",
        "Do not rescue weak branches by editing their traditional rules after looking at this history. If regime dependence is strong, the next framework should be registered under a new ID and should test whether symbolic states add information *conditional on independently defined market regimes*, with negative-control-adjusted promotion rules.",
        "",
    ]
    if manifest_text:
        lines.extend(["## Data manifest", "", "```json", manifest_text.strip(), "```", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate META_HIST_EXPANDING_2025_001 workers")
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

    manifest_path = args.input_dir / "manifest_baseline.json"
    manifest_text = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else None
    metadata = {
        "hypothesis_id": HYPOTHESIS_ID,
        "status": "RETROSPECTIVE_DESCRIPTIVE",
        "sessions": int(len(pred)),
        "first_date": pred["date"].min().strftime("%Y-%m-%d"),
        "last_date": pred["date"].max().strftime("%Y-%m-%d"),
        "models": list(MODELS),
        "procedure": "daily expanding refit with frozen inner-CV C selection",
        "negative_control": list(NEGATIVE_CONTROLS),
    }
    (args.out / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.out / "SUMMARY.md").write_text(
        _summary(pred, metrics, comparison, monthly, c_frequency, manifest_text), encoding="utf-8"
    )
    print((args.out / "SUMMARY.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
