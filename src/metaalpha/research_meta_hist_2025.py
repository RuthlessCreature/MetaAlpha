from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

from .data_sources import DataManifest, fetch_akshare_index
from .hybrid_model import (
    block_bootstrap_mean_improvement_probability,
    evaluate_probabilities,
    fit_predict_probability,
    rowwise_brier,
    rowwise_log_loss,
)
from .market_baseline import BASE_CATEGORICAL, BASE_CONTINUOUS, TARGET_DIRECTION, TARGET_RETURN
from .meta_branch import META_CANDIDATE_FEATURES, META_NEGATIVE_CONTROL_FEATURES, build_meta_historical_dataset


HYPOTHESIS_ID = "META_HIST_2025_001"
DEFAULT_RAW_START = "19901219"
DEFAULT_TEST_START = "20250101"
DEFAULT_END = "20260817"
BOOTSTRAP_BLOCK = 20
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 20260818

CANDIDATES = tuple(META_CANDIDATE_FEATURES)
NEGATIVE_CONTROLS = tuple(META_NEGATIVE_CONTROL_FEATURES)
ALL_BRANCHES = CANDIDATES + NEGATIVE_CONTROLS


def _branch_features(branch: str) -> list[str]:
    if branch in META_CANDIDATE_FEATURES:
        return list(META_CANDIDATE_FEATURES[branch])
    return list(META_NEGATIVE_CONTROL_FEATURES[branch])


def _metric_row(slice_id: str, model_id: str, metrics) -> dict[str, object]:
    row = asdict(metrics)
    row.update({"slice": slice_id, "model_id": model_id})
    return row


def _fit_once(train: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    y = test[TARGET_DIRECTION].astype(int).to_numpy()
    returns = test[TARGET_RETURN].astype(float).to_numpy()

    predictions = pd.DataFrame(
        {
            "date": test["date"].to_numpy(),
            "target": y,
            "same_session_return": returns,
        }
    )
    chosen_rows: list[dict[str, object]] = []
    tuning_parts: list[pd.DataFrame] = []

    p, best_c, tuning = fit_predict_probability(
        train,
        test,
        numeric_cols=list(BASE_CONTINUOUS),
        categorical_cols=list(BASE_CATEGORICAL),
        target_col=TARGET_DIRECTION,
    )
    predictions["baseline_prob"] = p
    chosen_rows.append({"model_id": "baseline", "best_C": best_c, "train_n": len(train), "test_n": len(test)})
    tuning = tuning.copy()
    tuning.insert(0, "model_id", "baseline")
    tuning_parts.append(tuning)

    for branch in ALL_BRANCHES:
        p, best_c, tuning = fit_predict_probability(
            train,
            test,
            numeric_cols=list(BASE_CONTINUOUS),
            categorical_cols=list(BASE_CATEGORICAL) + _branch_features(branch),
            target_col=TARGET_DIRECTION,
        )
        predictions[f"{branch}_prob"] = p
        chosen_rows.append({"model_id": branch, "best_C": best_c, "train_n": len(train), "test_n": len(test)})
        tuning = tuning.copy()
        tuning.insert(0, "model_id", branch)
        tuning_parts.append(tuning)

    return predictions, pd.DataFrame(chosen_rows), pd.concat(tuning_parts, ignore_index=True)


def _evaluate_slice(df: pd.DataFrame, slice_id: str) -> list[dict[str, object]]:
    if df.empty:
        return []
    y = df["target"].astype(int).to_numpy()
    returns = df["same_session_return"].astype(float).to_numpy()
    rows = [_metric_row(slice_id, "baseline", evaluate_probabilities(y, df["baseline_prob"].to_numpy(float), returns))]
    for branch in ALL_BRANCHES:
        rows.append(_metric_row(slice_id, branch, evaluate_probabilities(y, df[f"{branch}_prob"].to_numpy(float), returns)))
    return rows


def _slice_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    rows.extend(_evaluate_slice(predictions, "full_2025_to_end"))

    years = predictions["date"].dt.year
    for year in sorted(years.unique()):
        rows.extend(_evaluate_slice(predictions.loc[years == year], f"year_{year}"))

    quarters = predictions["date"].dt.to_period("Q")
    for quarter in sorted(quarters.unique()):
        rows.extend(_evaluate_slice(predictions.loc[quarters == quarter], f"quarter_{quarter}"))

    return pd.DataFrame(rows)


def _comparison(predictions: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    y = predictions["target"].astype(int).to_numpy()
    returns = predictions["same_session_return"].astype(float).to_numpy()
    base_p = predictions["baseline_prob"].to_numpy(float)
    base_metrics = evaluate_probabilities(y, base_p, returns)
    base_ll = rowwise_log_loss(y, base_p)
    base_br = rowwise_brier(y, base_p)

    rows: list[dict[str, object]] = []
    for i, branch in enumerate(ALL_BRANCHES):
        p = predictions[f"{branch}_prob"].to_numpy(float)
        m = evaluate_probabilities(y, p, returns)
        ll_imp = base_ll - rowwise_log_loss(y, p)
        br_imp = base_br - rowwise_brier(y, p)
        ll_prob, ll_lo, ll_hi = block_bootstrap_mean_improvement_probability(
            ll_imp,
            block_size=BOOTSTRAP_BLOCK,
            repetitions=BOOTSTRAP_REPS,
            seed=BOOTSTRAP_SEED + i * 2,
        )
        br_prob, br_lo, br_hi = block_bootstrap_mean_improvement_probability(
            br_imp,
            block_size=BOOTSTRAP_BLOCK,
            repetitions=BOOTSTRAP_REPS,
            seed=BOOTSTRAP_SEED + i * 2 + 1,
        )
        rows.append(
            {
                "model_id": branch,
                "negative_control": int(branch in NEGATIVE_CONTROLS),
                "logloss_improvement_vs_baseline": float(base_metrics.log_loss - m.log_loss),
                "brier_improvement_vs_baseline": float(base_metrics.brier_score - m.brier_score),
                "auc_delta_vs_baseline": float(m.roc_auc - base_metrics.roc_auc),
                "accuracy_delta_vs_baseline": float(m.accuracy - base_metrics.accuracy),
                "spread_return_delta_vs_baseline": float(m.probability_spread_return - base_metrics.probability_spread_return),
                "bootstrap_logloss_probability_positive": ll_prob,
                "bootstrap_logloss_ci025": ll_lo,
                "bootstrap_logloss_ci975": ll_hi,
                "bootstrap_brier_probability_positive": br_prob,
                "bootstrap_brier_ci025": br_lo,
                "bootstrap_brier_ci975": br_hi,
                "mean_prob_up": float(np.mean(p)),
                "forecast_up_rate": float(np.mean(p >= 0.5)),
            }
        )
    return pd.DataFrame(rows).sort_values("logloss_improvement_vs_baseline", ascending=False).reset_index(drop=True)


def _summary_markdown(
    train: pd.DataFrame,
    test: pd.DataFrame,
    metrics: pd.DataFrame,
    comparison: pd.DataFrame,
    chosen_c: pd.DataFrame,
    manifest: DataManifest | None,
) -> str:
    full = metrics.loc[metrics["slice"] == "full_2025_to_end"].copy()
    full = full[["model_id", "n", "log_loss", "brier_score", "roc_auc", "accuracy", "calibration_slope", "probability_spread_return"]]
    comparison_show = comparison[[
        "model_id",
        "negative_control",
        "logloss_improvement_vs_baseline",
        "brier_improvement_vs_baseline",
        "auc_delta_vs_baseline",
        "accuracy_delta_vs_baseline",
        "bootstrap_logloss_probability_positive",
        "bootstrap_brier_probability_positive",
    ]]
    yearly = metrics.loc[metrics["slice"].str.startswith("year_")].copy()
    yearly = yearly[["slice", "model_id", "n", "log_loss", "brier_score", "roc_auc", "accuracy"]]

    lines = [
        "# META_HIST_2025_001 — 2025+ Retrospective Holdout Diagnostic",
        "",
        "**Evidence status: RETROSPECTIVE / DESCRIPTIVE ONLY.** The model fit uses only pre-2025 eligible rows, but the symbolic candidate family itself was selected after these historical outcomes existed. Nothing here can alter or rescue `META_FWD_001`.",
        "",
        f"Training rows: **{len(train):,}** ({train['date'].min().date()} .. {train['date'].max().date()})",
        f"Test rows: **{len(test):,}** ({test['date'].min().date()} .. {test['date'].max().date()})",
        "Prediction target: same-session close-to-close direction; 09:25 information convention; all market predictors lagged to information known by t-1 close.",
        "",
        "## Full 2025+ metrics",
        "",
        tabulate(full, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Increment versus identical baseline test rows",
        "",
        tabulate(comparison_show, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Frozen C selected using pre-2025 training only",
        "",
        tabulate(chosen_c, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Calendar-year slices",
        "",
        tabulate(yearly, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Interpretation",
        "",
        "- Lower LogLoss and Brier are better; positive improvement columns mean the symbolic model beats the ordinary market baseline.",
        "- AUC and accuracy are secondary diagnostics; one historical period is not evidence of causal or metaphysical validity.",
        "- `liuyao_hash` is a deterministic negative control. If it looks as good as or better than traditional branches, that weakens any symbolic interpretation.",
        "- No PASS/FAIL gate is defined for this retrospective experiment.",
        "",
    ]
    if manifest is not None:
        lines.extend(["## Data manifest", "", "```json", manifest.to_json(), "```", ""])
    return "\n".join(lines)


def run(
    raw: pd.DataFrame,
    *,
    test_start: str,
    test_end: str,
    manifest: DataManifest | None = None,
    out_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    dataset = build_meta_historical_dataset(raw)
    start_ts = pd.Timestamp(test_start)
    end_ts = pd.Timestamp(test_end)
    train = dataset.loc[dataset["date"] < start_ts].copy().sort_values("date").reset_index(drop=True)
    test = dataset.loc[(dataset["date"] >= start_ts) & (dataset["date"] <= end_ts)].copy().sort_values("date").reset_index(drop=True)
    if len(train) < 1000:
        raise ValueError("insufficient pre-2025 training history")
    if len(test) < 100:
        raise ValueError("insufficient 2025+ test history")

    predictions, chosen_c, tuning = _fit_once(train, test)
    predictions["date"] = pd.to_datetime(predictions["date"]).dt.normalize()
    metrics = _slice_metrics(predictions)
    comparison = _comparison(predictions, metrics)

    outputs = {
        "predictions": predictions,
        "metrics_by_slice": metrics,
        "comparison_vs_baseline": comparison,
        "chosen_c": chosen_c,
        "inner_tuning": tuning,
    }

    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, table in outputs.items():
            table.to_csv(out_dir / f"{name}.csv", index=False)
        metadata = {
            "hypothesis_id": HYPOTHESIS_ID,
            "status": "RETROSPECTIVE_DESCRIPTIVE",
            "test_start": start_ts.strftime("%Y-%m-%d"),
            "test_end": end_ts.strftime("%Y-%m-%d"),
            "train_last_date": train["date"].iloc[-1].strftime("%Y-%m-%d"),
            "training_rows": int(len(train)),
            "test_rows": int(len(test)),
            "models": ["baseline", *ALL_BRANCHES],
            "negative_controls": list(NEGATIVE_CONTROLS),
            "bootstrap_block": BOOTSTRAP_BLOCK,
            "bootstrap_repetitions": BOOTSTRAP_REPS,
            "note": "Historical diagnostic only; candidate family selection postdates these outcomes.",
        }
        (out_dir / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if manifest is not None:
            (out_dir / "data_manifest.json").write_text(manifest.to_json() + "\n", encoding="utf-8")
        (out_dir / "SUMMARY.md").write_text(
            _summary_markdown(train, test, metrics, comparison, chosen_c, manifest), encoding="utf-8"
        )
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run META_HIST_2025_001 retrospective 2025+ diagnostic")
    parser.add_argument("--provider", default="sina")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--raw-start", default=DEFAULT_RAW_START)
    parser.add_argument("--test-start", default=DEFAULT_TEST_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    raw, manifest = fetch_akshare_index(
        symbol=args.symbol,
        start_date=args.raw_start,
        end_date=args.end,
        provider=args.provider,
    )
    run(raw, test_start=args.test_start, test_end=args.end, manifest=manifest, out_dir=args.out)
    print((args.out / "SUMMARY.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
