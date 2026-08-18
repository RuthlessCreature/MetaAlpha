from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

from .hybrid_model import evaluate_probabilities


EXPERIMENT_ID = "META_ROUTER_2025_001"
ALL_EXPERTS = ("baseline", "cycle", "ziping", "qimen", "meihua", "liuyao_hash")
TRAD_EXPERTS = ("baseline", "cycle", "ziping", "qimen", "meihua")


def _run_hedge(df: pd.DataFrame, experts: tuple[str, ...], router_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    k = len(experts)
    weights = np.ones(k, dtype=float) / k
    rows: list[dict[str, object]] = []
    weight_rows: list[dict[str, object]] = []

    for t, row in enumerate(df.itertuples(index=False), start=1):
        probs = np.array([float(getattr(row, f"{e}_prob")) for e in experts], dtype=float)
        p_router = float(np.dot(weights, probs))
        y = int(row.target)
        rows.append({
            "date": row.date,
            "router_id": router_id,
            "prob_up": p_router,
            "target": y,
            "same_session_return": float(row.same_session_return),
        })
        wr = {"date": row.date, "router_id": router_id}
        for i, expert in enumerate(experts):
            wr[f"weight_{expert}"] = float(weights[i])
        weight_rows.append(wr)

        losses = (probs - y) ** 2
        eta = float(np.sqrt(2.0 * np.log(k) / t))
        weights = weights * np.exp(-eta * losses)
        total = float(weights.sum())
        if not np.isfinite(total) or total <= 0.0:
            raise ValueError("invalid Hedge weight normalization")
        weights /= total

    return pd.DataFrame(rows), pd.DataFrame(weight_rows)


def _metric_row(model_id: str, y: np.ndarray, p: np.ndarray, returns: np.ndarray) -> dict[str, object]:
    m = evaluate_probabilities(y, p, returns)
    return {
        "model_id": model_id,
        "n": int(m.n),
        "log_loss": float(m.log_loss),
        "brier_score": float(m.brier_score),
        "roc_auc": float(m.roc_auc),
        "accuracy": float(m.accuracy),
        "calibration_slope": float(m.calibration_slope),
        "probability_spread_return": float(m.probability_spread_return),
    }


def run(predictions: pd.DataFrame, *, out_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    df = predictions.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise").dt.normalize()
    df = df.sort_values("date").reset_index(drop=True)
    required = ["date", "target", "same_session_return", *[f"{e}_prob" for e in ALL_EXPERTS]]
    df = df.dropna(subset=required).copy().reset_index(drop=True)
    if len(df) < 300:
        raise ValueError("router diagnostic requires at least 300 rows")

    all_pred, all_weights = _run_hedge(df, ALL_EXPERTS, "hedge_all_v1")
    trad_pred, trad_weights = _run_hedge(df, TRAD_EXPERTS, "hedge_traditional_v1")

    y = df["target"].astype(int).to_numpy()
    returns = df["same_session_return"].astype(float).to_numpy()
    metrics: list[dict[str, object]] = []
    for expert in ALL_EXPERTS:
        metrics.append(_metric_row(expert, y, df[f"{expert}_prob"].to_numpy(float), returns))
    metrics.append(_metric_row("hedge_all_v1", y, all_pred["prob_up"].to_numpy(float), returns))
    metrics.append(_metric_row("hedge_traditional_v1", y, trad_pred["prob_up"].to_numpy(float), returns))
    metric_df = pd.DataFrame(metrics).sort_values("log_loss").reset_index(drop=True)

    router_predictions = pd.concat([all_pred, trad_pred], ignore_index=True)
    weights = pd.concat([all_weights, trad_weights], ignore_index=True)

    # Calendar-year metrics for routers and baseline.
    year_rows: list[dict[str, object]] = []
    for year in sorted(df["date"].dt.year.unique()):
        mask = df["date"].dt.year == year
        yy = y[mask.to_numpy()]
        rr = returns[mask.to_numpy()]
        year_rows.append({"year": int(year), **_metric_row("baseline", yy, df.loc[mask, "baseline_prob"].to_numpy(float), rr)})
        for router_id, pred in (("hedge_all_v1", all_pred), ("hedge_traditional_v1", trad_pred)):
            rp = pred.loc[pd.to_datetime(pred["date"]).dt.year == year, "prob_up"].to_numpy(float)
            year_rows.append({"year": int(year), **_metric_row(router_id, yy, rp, rr)})
    year_metrics = pd.DataFrame(year_rows)

    # End weights and maximum weight reached by each expert are useful diagnostics.
    summary_weights: list[dict[str, object]] = []
    for router_id, experts, wdf in (
        ("hedge_all_v1", ALL_EXPERTS, all_weights),
        ("hedge_traditional_v1", TRAD_EXPERTS, trad_weights),
    ):
        last = wdf.iloc[-1]
        for expert in experts:
            col = f"weight_{expert}"
            summary_weights.append({
                "router_id": router_id,
                "expert": expert,
                "ending_weight": float(last[col]),
                "max_weight": float(wdf[col].max()),
                "min_weight": float(wdf[col].min()),
            })
    weight_summary = pd.DataFrame(summary_weights)

    outputs = {
        "metrics": metric_df,
        "year_metrics": year_metrics,
        "router_predictions": router_predictions,
        "weights": weights,
        "weight_summary": weight_summary,
    }

    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, table in outputs.items():
            table.to_csv(out_dir / f"{name}.csv", index=False)
        metadata = {
            "experiment_id": EXPERIMENT_ID,
            "status": "RETROSPECTIVE_TRACK_T",
            "rows": len(df),
            "first_date": df["date"].iloc[0].strftime("%Y-%m-%d"),
            "last_date": df["date"].iloc[-1].strftime("%Y-%m-%d"),
            "update_loss": "Brier",
            "eta_t": "sqrt(2*ln(K)/t)",
            "timing": "weights entering t predict t; update only after t outcome",
        }
        (out_dir / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        show_metrics = metric_df[["model_id", "n", "log_loss", "brier_score", "roc_auc", "accuracy"]]
        lines = [
            f"# {EXPERIMENT_ID} — Past-only online expert router",
            "",
            "**RETROSPECTIVE / TRACK T ONLY. Not evidence for metaphysical validity.**",
            "",
            "Routers use equal initial weights. Session t uses weights available before t; only after t settles are weights updated using expert Brier losses. Learning rate is parameter-free `sqrt(2 ln K / t)`.",
            "",
            "## Full-period metrics",
            "",
            tabulate(show_metrics, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
            "",
            "## Router calendar-year metrics",
            "",
            tabulate(year_metrics[["year", "model_id", "n", "log_loss", "brier_score", "roc_auc", "accuracy"]], headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
            "",
            "## Router weight diagnostics",
            "",
            tabulate(weight_summary, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
            "",
            "Interpretation: if the all-expert router wins while allocating material weight to synthetic/hash experts, that supports adaptive time-encoding utility only. If the traditional-only router wins independently, that is still historical and requires a new future experiment.",
            "",
        ]
        (out_dir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=EXPERIMENT_ID)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    predictions = pd.read_csv(args.predictions)
    run(predictions, out_dir=args.out)
    print((args.out / "SUMMARY.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
