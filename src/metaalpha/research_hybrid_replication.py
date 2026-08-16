from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

from .calendar_cycle import add_calendar_cycle_features
from .data_sources import DataManifest, fetch_akshare_index
from .hybrid_model import (
    block_bootstrap_mean_improvement_probability,
    evaluate_probabilities,
    fit_predict_probability,
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
from .research_hybrid_alpha import OUTER_WINDOWS, SYMBOLIC_BLOCKS, _outer_train_test


HYPOTHESIS_ID = "HYBRID_REPL_001"
PROVIDER = "sina"
HISTORICAL_END = "20260814"
CANDIDATES = ("cycle", "ziping")
BOOTSTRAP_BLOCK = 20
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 20260816

INDEX_CONFIG = (
    ("sse50", "SSE 50", "sh000016"),
    ("csi300", "CSI 300", "sh000300"),
    ("csi500", "CSI 500", "sh000905"),
    ("sz_component", "Shenzhen Component", "sz399001"),
)


def build_replication_dataset(raw: pd.DataFrame) -> pd.DataFrame:
    out = add_market_baseline_features(raw)
    out = build_dataset(out, include_ziping=True, include_natal_transit=False)
    out = add_calendar_cycle_features(out)
    required = [
        "date",
        TARGET_DIRECTION,
        TARGET_RETURN,
        *BASE_CONTINUOUS,
        *BASE_CATEGORICAL,
        *SYMBOLIC_BLOCKS["cycle"],
        *SYMBOLIC_BLOCKS["ziping"],
    ]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"replication dataset missing registered columns: {missing}")
    out = out.dropna(subset=required).copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.normalize()
    out[TARGET_DIRECTION] = out[TARGET_DIRECTION].astype(int)
    return out.sort_values("date").reset_index(drop=True)


def _metric_row(window: str, model_id: str, metrics) -> dict[str, object]:
    return {
        "window": window,
        "model_id": model_id,
        "n": metrics.n,
        "log_loss": metrics.log_loss,
        "brier_score": metrics.brier_score,
        "roc_auc": metrics.roc_auc,
        "accuracy": metrics.accuracy,
        "calibration_slope": metrics.calibration_slope,
        "probability_spread_return": metrics.probability_spread_return,
    }


def _run_index_walk_forward(df: pd.DataFrame):
    pred_parts: list[pd.DataFrame] = []
    metric_rows: list[dict[str, object]] = []
    c_rows: list[dict[str, object]] = []

    for window, start, end in OUTER_WINDOWS:
        train, test = _outer_train_test(df, start, end)
        y = test[TARGET_DIRECTION].to_numpy(int)
        returns = test[TARGET_RETURN].to_numpy(float)

        base_p, base_c, _ = fit_predict_probability(
            train,
            test,
            numeric_cols=list(BASE_CONTINUOUS),
            categorical_cols=list(BASE_CATEGORICAL),
            target_col=TARGET_DIRECTION,
        )
        metric_rows.append(_metric_row(window, "baseline", evaluate_probabilities(y, base_p, returns)))
        c_rows.append({"window": window, "model_id": "baseline", "best_C": base_c, "train_n": len(train), "test_n": len(test)})

        pred = pd.DataFrame(
            {
                "date": test["date"].to_numpy(),
                "window": window,
                "target": y,
                "same_session_return": returns,
                "baseline_prob": base_p,
            }
        )
        for model_id in CANDIDATES:
            p, best_c, _ = fit_predict_probability(
                train,
                test,
                numeric_cols=list(BASE_CONTINUOUS),
                categorical_cols=list(BASE_CATEGORICAL) + SYMBOLIC_BLOCKS[model_id],
                target_col=TARGET_DIRECTION,
            )
            metric_rows.append(_metric_row(window, model_id, evaluate_probabilities(y, p, returns)))
            c_rows.append({"window": window, "model_id": model_id, "best_C": best_c, "train_n": len(train), "test_n": len(test)})
            pred[f"{model_id}_prob"] = p
        pred_parts.append(pred)

    return (
        pd.concat(pred_parts, ignore_index=True).sort_values("date").reset_index(drop=True),
        pd.DataFrame(metric_rows),
        pd.DataFrame(c_rows),
    )


def _evaluate_index_gate(predictions: pd.DataFrame, window_metrics: pd.DataFrame) -> pd.DataFrame:
    y = predictions["target"].to_numpy(int)
    returns = predictions["same_session_return"].to_numpy(float)
    base_p = predictions["baseline_prob"].to_numpy(float)
    base = evaluate_probabilities(y, base_p, returns)
    base_ll = rowwise_log_loss(y, base_p)
    base_br = rowwise_brier(y, base_p)

    rows: list[dict[str, object]] = []
    p_ll: dict[str, float] = {}
    p_br: dict[str, float] = {}
    for model_id in CANDIDATES:
        p = predictions[f"{model_id}_prob"].to_numpy(float)
        aug = evaluate_probabilities(y, p, returns)
        ll_imp = base_ll - rowwise_log_loss(y, p)
        br_imp = base_br - rowwise_brier(y, p)
        ll_prob, ll_lo, ll_hi = block_bootstrap_mean_improvement_probability(
            ll_imp, block_size=BOOTSTRAP_BLOCK, repetitions=BOOTSTRAP_REPS, seed=BOOTSTRAP_SEED
        )
        br_prob, br_lo, br_hi = block_bootstrap_mean_improvement_probability(
            br_imp, block_size=BOOTSTRAP_BLOCK, repetitions=BOOTSTRAP_REPS, seed=BOOTSTRAP_SEED + 1
        )
        p_ll[model_id] = 1.0 - ll_prob
        p_br[model_id] = 1.0 - br_prob

        ll_wins = 0
        br_wins = 0
        for window, _, _ in OUTER_WINDOWS:
            b = window_metrics.loc[(window_metrics["window"] == window) & (window_metrics["model_id"] == "baseline")].iloc[0]
            a = window_metrics.loc[(window_metrics["window"] == window) & (window_metrics["model_id"] == model_id)].iloc[0]
            ll_wins += int(float(a["log_loss"]) < float(b["log_loss"]))
            br_wins += int(float(a["brier_score"]) < float(b["brier_score"]))

        rows.append(
            {
                "model_id": model_id,
                "logloss_improvement": float(base.log_loss - aug.log_loss),
                "brier_improvement": float(base.brier_score - aug.brier_score),
                "auc_delta": float(aug.roc_auc - base.roc_auc),
                "windows_logloss_improved": ll_wins,
                "windows_brier_improved": br_wins,
                "bootstrap_logloss_probability_positive": ll_prob,
                "bootstrap_brier_probability_positive": br_prob,
                "bootstrap_logloss_ci025": ll_lo,
                "bootstrap_logloss_ci975": ll_hi,
                "bootstrap_brier_ci025": br_lo,
                "bootstrap_brier_ci975": br_hi,
                "bootstrap_logloss_p_one_sided": 1.0 - ll_prob,
                "bootstrap_brier_p_one_sided": 1.0 - br_prob,
            }
        )

    out = pd.DataFrame(rows)
    holm_ll = holm_adjust(p_ll)
    holm_br = holm_adjust(p_br)
    out["bootstrap_logloss_p_holm"] = out["model_id"].map(holm_ll)
    out["bootstrap_brier_p_holm"] = out["model_id"].map(holm_br)
    out["gate_pass"] = (
        (out["windows_logloss_improved"] >= 3)
        & (out["windows_brier_improved"] >= 3)
        & (out["logloss_improvement"] >= 0.001)
        & (out["brier_improvement"] >= 0.0005)
        & (out["auc_delta"] >= -0.005)
        & (out["bootstrap_logloss_probability_positive"] >= 0.95)
        & (out["bootstrap_brier_probability_positive"] >= 0.95)
        & (out["bootstrap_logloss_p_holm"] <= 0.05)
        & (out["bootstrap_brier_p_holm"] <= 0.05)
    ).astype(int)
    return out


def replication_decision(index_gate_rows: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model_id in CANDIDATES:
        x = index_gate_rows.loc[index_gate_rows["model_id"] == model_id]
        passes = int(x["gate_pass"].sum())
        rows.append(
            {
                "model_id": model_id,
                "indices_evaluated": int(len(x)),
                "indices_passed": passes,
                "required_indices_passed": 3,
                "replication_pass": int(len(x) == 4 and passes >= 3),
            }
        )
    return pd.DataFrame(rows)


def run_replication(out_dir: Path) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    all_gate: list[pd.DataFrame] = []
    all_metrics: list[pd.DataFrame] = []
    all_c: list[pd.DataFrame] = []
    manifest_rows: list[dict[str, object]] = []

    for index_id, index_name, provider_symbol in INDEX_CONFIG:
        raw, manifest = fetch_akshare_index(
            symbol=provider_symbol,
            start_date="19901219",
            end_date=HISTORICAL_END,
            provider=PROVIDER,
        )
        dataset = build_replication_dataset(raw)
        predictions, metrics, chosen_c = _run_index_walk_forward(dataset)
        gate = _evaluate_index_gate(predictions, metrics)

        for table in (predictions, metrics, chosen_c, gate):
            table.insert(0, "index_id", index_id)
            table.insert(1, "index_name", index_name)
        all_gate.append(gate)
        all_metrics.append(metrics)
        all_c.append(chosen_c)

        index_dir = out_dir / index_id
        index_dir.mkdir(parents=True, exist_ok=True)
        dataset.to_csv(index_dir / "dataset.csv", index=False)
        predictions.to_csv(index_dir / "predictions.csv", index=False)
        metrics.to_csv(index_dir / "window_metrics.csv", index=False)
        chosen_c.to_csv(index_dir / "chosen_c.csv", index=False)
        gate.to_csv(index_dir / "gate.csv", index=False)
        (index_dir / "data_manifest.json").write_text(manifest.to_json(), encoding="utf-8")
        manifest_rows.append({"index_id": index_id, "index_name": index_name, **json.loads(manifest.to_json()), "eligible_rows": len(dataset), "oos_rows": len(predictions)})

    gate_all = pd.concat(all_gate, ignore_index=True)
    metrics_all = pd.concat(all_metrics, ignore_index=True)
    c_all = pd.concat(all_c, ignore_index=True)
    manifests = pd.DataFrame(manifest_rows)
    decision = replication_decision(gate_all)

    gate_all.to_csv(out_dir / "index_gates.csv", index=False)
    metrics_all.to_csv(out_dir / "window_metrics_all.csv", index=False)
    c_all.to_csv(out_dir / "chosen_c_all.csv", index=False)
    manifests.to_csv(out_dir / "data_manifests.csv", index=False)
    decision.to_csv(out_dir / "replication_decision.csv", index=False)

    summary = [
        "# HYBRID_REPL_001 — Cross-index replication",
        "",
        "**Evidence status: preregistered external-index historical replication. Shanghai Composite is not counted.**",
        "",
        "Frozen cycle and ziping models are evaluated without feature/model/gate changes on SSE 50, CSI 300, CSI 500 and Shenzhen Component. A model replicates only if at least 3 of 4 indices pass the complete per-index gate.",
        "",
        "## Replication decision",
        "",
        tabulate(decision, headers="keys", tablefmt="github", showindex=False),
        "",
        "## Per-index gates",
        "",
        tabulate(gate_all, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
        "",
        "## Data manifests",
        "",
        tabulate(manifests[["index_id", "symbol", "first_date", "last_date", "rows", "eligible_rows", "oos_rows", "canonical_sha256"]], headers="keys", tablefmt="github", showindex=False),
        "",
    ]
    (out_dir / "SUMMARY.md").write_text("\n".join(summary), encoding="utf-8")
    metadata = {
        "hypothesis_id": HYPOTHESIS_ID,
        "status": "PREREGISTERED_EXTERNAL_INDEX_REPLICATION",
        "provider_required": PROVIDER,
        "indices": [x[0] for x in INDEX_CONFIG],
        "candidates": list(CANDIDATES),
        "required_indices_passed": 3,
        "replication_passes": int(decision["replication_pass"].sum()),
    }
    (out_dir / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"index_gates": gate_all, "replication_decision": decision, "manifests": manifests}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run preregistered HYBRID_REPL_001")
    parser.add_argument("--out", type=Path, default=Path("reports/hybrid_replication"))
    args = parser.parse_args()
    outputs = run_replication(args.out)
    print(outputs["replication_decision"].to_string(index=False))
    print(f"report={args.out / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
