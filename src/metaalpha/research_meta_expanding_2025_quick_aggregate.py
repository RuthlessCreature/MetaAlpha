from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from tabulate import tabulate

from .research_meta_expanding_2025_aggregate import (
    CANDIDATES,
    NEGATIVE_CONTROLS,
    _advantage_curves,
    _c_frequency,
    _comparison,
    _load_workers,
    _monthly_leaders,
    _slice_metrics,
)


HYPOTHESIS_ID = "META_HIST_EXPANDING_C001_2025_001"


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate fixed-C=0.01 daily expanding quick diagnostic")
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
    latest = curves.iloc[-1]
    roll_rows = []
    for model in (*CANDIDATES, *NEGATIVE_CONTROLS):
        roll_rows.append({
            "model_id": model,
            "cum_logloss_advantage": latest[f"{model}_cum_logloss_advantage"],
            "roll20_ll_improvement": latest[f"{model}_roll20_logloss_improvement"],
            "roll60_ll_improvement": latest[f"{model}_roll60_logloss_improvement"],
            "roll120_ll_improvement": latest[f"{model}_roll120_logloss_improvement"],
        })
    rolling = pd.DataFrame(roll_rows).sort_values("cum_logloss_advantage", ascending=False)

    lines = [
        "# META_HIST_EXPANDING_C001_2025_001 — Fixed-C Daily Expanding Quick Diagnostic",
        "",
        "**Evidence status: RETROSPECTIVE / DESCRIPTIVE / QUICK APPROXIMATION.**",
        "",
        "Each trading day is refitted on all prior eligible rows, but C is fixed at **0.01** instead of being re-selected by inner CV every day. C=0.01 was selected for all six models in the pre-2025 fixed-fit diagnostic. The exact daily-tuned reconstruction is a separate experiment.",
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
        "## Latest cumulative / rolling LogLoss advantage",
        "",
        tabulate(rolling, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Negative-control regime diagnostic",
        "",
        f"The hash negative control beat the best traditional candidate in **{control_wins}/{len(monthly)} months** by monthly LogLoss improvement.",
        "",
        "This quick run is intended to reveal whether daily adaptation materially changes the regime pattern. It must not be used to alter META_FWD_001.",
        "",
    ]
    (args.out / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    (args.out / "run_metadata.json").write_text(json.dumps({
        "hypothesis_id": HYPOTHESIS_ID,
        "status": "RETROSPECTIVE_DESCRIPTIVE_QUICK_APPROXIMATION",
        "sessions": int(len(pred)),
        "fixed_C": 0.01,
        "procedure": "daily expanding refit, C fixed at 0.01",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print((args.out / "SUMMARY.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
