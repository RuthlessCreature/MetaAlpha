from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

from .calendar_cycle import add_calendar_cycle_features
from .data_sources import DataManifest, fetch_akshare_index
from .hybrid_model import (
    evaluate_probabilities,
    fit_predict_probability,
    block_bootstrap_mean_improvement_probability,
    holm_adjust,
    rowwise_brier,
    rowwise_log_loss,
)
from .market_baseline import (
    BASE_CATEGORICAL,
    BASE_CONTINUOUS,
    TARGET_DIRECTION,
    TARGET_RETURN,
    add_market_baseline_features,
)
from .pipeline import build_dataset
from .qimen_market import add_qimen_market_features


HYPOTHESIS_ID = "HYBRID_ALPHA_001"
HISTORICAL_END = "2026-08-14"
BOOTSTRAP_BLOCK = 20
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 20260816

OUTER_WINDOWS = (
    ("wf_2010_2013", "2010-01-01", "2013-12-31"),
    ("wf_2014_2017", "2014-01-01", "2017-12-31"),
    ("wf_2018_2021", "2018-01-01", "2021-12-31"),
    ("wf_2022_2026", "2022-01-01", HISTORICAL_END),
)

SYMBOLIC_BLOCKS: dict[str, list[str]] = {
    "cycle": [
        "cycle__v1__prev_jieqi",
        "cycle__v1__jieqi_phase_quartile",
        "cycle__v1__day_pillar",
        "cycle__v1__month_stem",
        "cycle__v1__month_branch",
    ],
    "qimen": [
        "qimen__v1__dun_ju_yuan",
        "qimen__v1__duty_star_door",
        "qimen__v1__duty_landings",
        "qimen__v1__rotation_state",
        "qimen__v1__void_relation_state",
        "qimen__v1__yima_relation_state",
    ],
    "ziping": [
        "zpzt_use__v2__selected_ten_god",
        "zpzt_use__v2__selection_mode",
        "zpzt_route__v3__route_state",
        "zpzt_structure__v4__wealth_resource_position_resolution",
        "zpzt_structure__v4__selected_use_root_bin",
        "zpzt_structure__v4__support_profile",
    ],
}
SYMBOLIC_BLOCKS["all_symbolic"] = list(
    dict.fromkeys(SYMBOLIC_BLOCKS["cycle"] + SYMBOLIC_BLOCKS["qimen"] + SYMBOLIC_BLOCKS["ziping"])
)


def build_hybrid_dataset(raw: pd.DataFrame) -> pd.DataFrame:
    out = add_market_baseline_features(raw)
    out = build_dataset(out, include_ziping=True, include_natal_transit=False)
    out = add_calendar_cycle_features(out)
    out = add_qimen_market_features(out)
    return out.sort_values("date").reset_index(drop=True)


def _all_required_columns() -> list[str]:
    symbolic_union = list(dict.fromkeys(sum(SYMBOLIC_BLOCKS.values(), [])))
    return [
        "date",
        TARGET_DIRECTION,
        TARGET_RETURN,
        *BASE_CONTINUOUS,
        *BASE_CATEGORICAL,
        *symbolic_union,
    ]


def common_eligible_dataset(dataset: pd.DataFrame) -> pd.DataFrame:
    required = _all_required_columns()
    missing = [c for c in required if c not in dataset.columns]
    if missing:
        raise ValueError(f"HYBRID_ALPHA_001 dataset missing registered columns: {missing}")
    out = dataset.dropna(subset=required).copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.normalize()
    out[TARGET_DIRECTION] = out[TARGET_DIRECTION].astype(int)
    return out.sort_values("date").reset_index(drop=True)


def _outer_train_test(df: pd.DataFrame, start: str, end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    train = df.loc[df["date"] < start_ts].copy().sort_values("date").reset_index(drop=True)
    test = df.loc[(df["date"] >= start_ts) & (df["date"] <= end_ts)].copy().sort_values("date").reset_index(drop=True)
    if len(train) < 500:
        raise ValueError(f"insufficient training rows before {start}")
    if len(test) < 100:
        raise ValueError(f"insufficient test rows in {start}..{end}")
    # Frozen one-session embargo.
    train = train.iloc[:-1].copy().reset_index(drop=True)
    return train, test


def _metric_row(window: str, model_id: str, metrics) -> dict[str, object]:
    row = asdict(metrics)
    row.update({"window": window, "model_id": model_id})
    return row


def _run_walk_forward(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prediction_parts: list[pd.DataFrame] = []
    metric_rows: list[dict[str, object]] = []
    tuning_rows: list[pd.DataFrame] = []
    c_rows: list[dict[str, object]] = []

    for window, start, end in OUTER_WINDOWS:
        train, test = _outer_train_test(df, start, end)
        y_test = test[TARGET_DIRECTION].astype(int).to_numpy()
        returns_test = test[TARGET_RETURN].astype(float).to_numpy()

        baseline_prob, baseline_c, tuning = fit_predict_probability(
            train,
            test,
            numeric_cols=list(BASE_CONTINUOUS),
            categorical_cols=list(BASE_CATEGORICAL),
            target_col=TARGET_DIRECTION,
        )
        tuning = tuning.copy()
        tuning.insert(0, "window", window)
        tuning.insert(1, "model_id", "baseline")
        tuning_rows.append(tuning)
        c_rows.append({"window": window, "model_id": "baseline", "best_C": baseline_c, "train_n": len(train), "test_n": len(test)})
        metric_rows.append(_metric_row(window, "baseline", evaluate_probabilities(y_test, baseline_prob, returns_test)))

        pred = pd.DataFrame(
            {
                "date": test["date"].to_numpy(),
                "window": window,
                "target": y_test,
                "same_session_return": returns_test,
                "baseline_prob": baseline_prob,
            }
        )

        for block_id, symbolic_cols in SYMBOLIC_BLOCKS.items():
            categorical = list(BASE_CATEGORICAL) + symbolic_cols
            p, best_c, tuning = fit_predict_probability(
                train,
                test,
                numeric_cols=list(BASE_CONTINUOUS),
                categorical_cols=categorical,
                target_col=TARGET_DIRECTION,
            )
            tuning = tuning.copy()
            tuning.insert(0, "window", window)
            tuning.insert(1, "model_id", block_id)
            tuning_rows.append(tuning)
            c_rows.append({"window": window, "model_id": block_id, "best_C": best_c, "train_n": len(train), "test_n": len(test)})
            metric_rows.append(_metric_row(window, block_id, evaluate_probabilities(y_test, p, returns_test)))
            pred[f"{block_id}_prob"] = p

        prediction_parts.append(pred)

    predictions = pd.concat(prediction_parts, ignore_index=True).sort_values("date").reset_index(drop=True)
    metrics = pd.DataFrame(metric_rows)
    tuning = pd.concat(tuning_rows, ignore_index=True)
    chosen_c = pd.DataFrame(c_rows)
    return predictions, metrics, tuning, chosen_c


def _aggregate_and_gate(predictions: pd.DataFrame, window_metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    y = predictions["target"].to_numpy(dtype=int)
    returns = predictions["same_session_return"].to_numpy(dtype=float)
    base_p = predictions["baseline_prob"].to_numpy(dtype=float)
    base_metrics = evaluate_probabilities(y, base_p, returns)

    aggregate_rows = [_metric_row("full_oos", "baseline", base_metrics)]
    comparison_rows: list[dict[str, object]] = []
    bootstrap_p_logloss: dict[str, float] = {}
    bootstrap_p_brier: dict[str, float] = {}

    base_ll_row = rowwise_log_loss(y, base_p)
    base_br_row = rowwise_brier(y, base_p)

    for block_id in SYMBOLIC_BLOCKS:
        p = predictions[f"{block_id}_prob"].to_numpy(dtype=float)
        metrics = evaluate_probabilities(y, p, returns)
        aggregate_rows.append(_metric_row("full_oos", block_id, metrics))

        ll_improvement_rows = base_ll_row - rowwise_log_loss(y, p)
        br_improvement_rows = base_br_row - rowwise_brier(y, p)
        ll_prob, ll_ci_lo, ll_ci_hi = block_bootstrap_mean_improvement_probability(
            ll_improvement_rows,
            block_size=BOOTSTRAP_BLOCK,
            repetitions=BOOTSTRAP_REPS,
            seed=BOOTSTRAP_SEED,
        )
        br_prob, br_ci_lo, br_ci_hi = block_bootstrap_mean_improvement_probability(
            br_improvement_rows,
            block_size=BOOTSTRAP_BLOCK,
            repetitions=BOOTSTRAP_REPS,
            seed=BOOTSTRAP_SEED + 1,
        )
        bootstrap_p_logloss[block_id] = 1.0 - ll_prob
        bootstrap_p_brier[block_id] = 1.0 - br_prob

        w = window_metrics.pivot(index="window", columns="model_id")
        ll_wins = 0
        br_wins = 0
        for window, _, _ in OUTER_WINDOWS:
            base_win = window_metrics.loc[(window_metrics["window"] == window) & (window_metrics["model_id"] == "baseline")].iloc[0]
            aug_win = window_metrics.loc[(window_metrics["window"] == window) & (window_metrics["model_id"] == block_id)].iloc[0]
            ll_wins += int(float(aug_win["log_loss"]) < float(base_win["log_loss"]))
            br_wins += int(float(aug_win["brier_score"]) < float(base_win["brier_score"]))

        comparison_rows.append(
            {
                "model_id": block_id,
                "logloss_improvement": float(base_metrics.log_loss - metrics.log_loss),
                "brier_improvement": float(base_metrics.brier_score - metrics.brier_score),
                "auc_delta": float(metrics.roc_auc - base_metrics.roc_auc),
                "accuracy_delta": float(metrics.accuracy - base_metrics.accuracy),
                "spread_return_delta": float(metrics.probability_spread_return - base_metrics.probability_spread_return),
                "windows_logloss_improved": ll_wins,
                "windows_brier_improved": br_wins,
                "bootstrap_logloss_probability_positive": ll_prob,
                "bootstrap_logloss_ci025": ll_ci_lo,
                "bootstrap_logloss_ci975": ll_ci_hi,
                "bootstrap_brier_probability_positive": br_prob,
                "bootstrap_brier_ci025": br_ci_lo,
                "bootstrap_brier_ci975": br_ci_hi,
                "bootstrap_logloss_p_one_sided": 1.0 - ll_prob,
                "bootstrap_brier_p_one_sided": 1.0 - br_prob,
            }
        )

    aggregate = pd.DataFrame(aggregate_rows)
    comparison = pd.DataFrame(comparison_rows)
    holm_ll = holm_adjust(bootstrap_p_logloss)
    holm_br = holm_adjust(bootstrap_p_brier)
    comparison["bootstrap_logloss_p_holm"] = comparison["model_id"].map(holm_ll)
    comparison["bootstrap_brier_p_holm"] = comparison["model_id"].map(holm_br)

    comparison["gate_pass"] = (
        (comparison["windows_logloss_improved"] >= 3)
        & (comparison["windows_brier_improved"] >= 3)
        & (comparison["logloss_improvement"] >= 0.001)
        & (comparison["brier_improvement"] >= 0.0005)
        & (comparison["auc_delta"] >= -0.005)
        & (comparison["bootstrap_logloss_probability_positive"] >= 0.95)
        & (comparison["bootstrap_brier_probability_positive"] >= 0.95)
        & (comparison["bootstrap_logloss_p_holm"] <= 0.05)
        & (comparison["bootstrap_brier_p_holm"] <= 0.05)
    ).astype(int)
    return aggregate, comparison


def _summary_markdown(
    manifest: DataManifest | None,
    dataset: pd.DataFrame,
    predictions: pd.DataFrame,
    metrics: pd.DataFrame,
    aggregate: pd.DataFrame,
    comparison: pd.DataFrame,
) -> str:
    lines = [
        "# HYBRID_ALPHA_001 — Symbolic Incremental OOS Exploration",
        "",
        "**Evidence status: EXPLORATORY OOS OVER PRE-EXISTING HISTORY. This is not a future holdout.**",
        "",
        "Prediction time is 09:25 Asia/Shanghai. Market predictors use information available no later than t-1 close; symbolic states are deterministic at t 09:25.",
        "",
        f"Eligible common rows: {len(dataset):,}",
        f"OOS prediction rows: {len(predictions):,}",
        f"Gate passes: {int(comparison['gate_pass'].sum())}",
        "",
        "## Full-OOS metrics",
        "",
        tabulate(aggregate, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Increment versus identical baseline OOS rows",
        "",
        tabulate(comparison, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Window metrics",
        "",
        tabulate(metrics, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Frozen gate",
        "",
        "A block must improve LogLoss and Brier in at least 3/4 windows, improve full-OOS LogLoss by >=0.001 and Brier by >=0.0005, avoid AUC degradation worse than 0.005, reach >=95% block-bootstrap probability of positive improvement for both primary losses, and retain Holm-adjusted one-sided p<=0.05 across the four symbolic blocks.",
        "",
    ]
    if manifest is not None:
        lines.extend(
            [
                "## Data manifest",
                "",
                "```json",
                manifest.to_json(),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def run_hybrid_alpha(raw: pd.DataFrame, *, manifest: DataManifest | None = None, out_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    dataset_full = build_hybrid_dataset(raw)
    dataset = common_eligible_dataset(dataset_full)
    predictions, metrics, tuning, chosen_c = _run_walk_forward(dataset)
    aggregate, comparison = _aggregate_and_gate(predictions, metrics)

    outputs = {
        "dataset": dataset,
        "predictions": predictions,
        "window_metrics": metrics,
        "aggregate_metrics": aggregate,
        "comparison_gate": comparison,
        "inner_tuning": tuning,
        "chosen_c": chosen_c,
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, table in outputs.items():
            table.to_csv(out_dir / f"{name}.csv", index=False)
        metadata = {
            "hypothesis_id": HYPOTHESIS_ID,
            "status": "EXPLORATORY_OOS_ALREADY_EXISTING_HISTORY",
            "provider_required": "sina",
            "historical_last_date": HISTORICAL_END,
            "market_anchor": "09:25 Asia/Shanghai",
            "models": ["baseline", *SYMBOLIC_BLOCKS.keys()],
            "outer_windows": list(OUTER_WINDOWS),
            "bootstrap_block": BOOTSTRAP_BLOCK,
            "bootstrap_repetitions": BOOTSTRAP_REPS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "gate_passes": int(comparison["gate_pass"].sum()),
        }
        (out_dir / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        if manifest is not None:
            (out_dir / "data_manifest.json").write_text(manifest.to_json(), encoding="utf-8")
        (out_dir / "SUMMARY.md").write_text(
            _summary_markdown(manifest, dataset, predictions, metrics, aggregate, comparison),
            encoding="utf-8",
        )
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run preregistered HYBRID_ALPHA_001 exploration")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--fetch-akshare", action="store_true")
    parser.add_argument("--provider", default="sina")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--start", default="19901219")
    parser.add_argument("--end", default="20260814")
    parser.add_argument("--out", type=Path, default=Path("reports/hybrid_alpha_exploratory"))
    args = parser.parse_args()

    if args.fetch_akshare:
        raw, manifest = fetch_akshare_index(
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
            provider=args.provider,
        )
    elif args.input is not None:
        raw = pd.read_csv(args.input)
        manifest = None
    else:
        raise SystemExit("use --fetch-akshare or --input")

    outputs = run_hybrid_alpha(raw, manifest=manifest, out_dir=args.out)
    comparison = outputs["comparison_gate"]
    print(f"eligible_rows={len(outputs['dataset'])}")
    print(f"oos_rows={len(outputs['predictions'])}")
    print(f"gate_passes={int(comparison['gate_pass'].sum())}")
    print(f"report={args.out / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
