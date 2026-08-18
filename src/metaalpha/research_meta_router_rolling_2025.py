from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

from .hybrid_model import evaluate_probabilities


EXPERIMENT_ID = "META_ROUTER_ROLLING_2025_001"
ALL_EXPERTS = ("baseline", "cycle", "ziping", "qimen", "meihua", "liuyao_hash")
TRAD_EXPERTS = ("baseline", "cycle", "ziping", "qimen", "meihua")
WINDOWS = (20, 60, 120)


def _run_router(df: pd.DataFrame, experts: tuple[str, ...], window: int, router_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    k = len(experts)
    loss_history: list[np.ndarray] = []
    pred_rows: list[dict[str, object]] = []
    weight_rows: list[dict[str, object]] = []

    for row in df.itertuples(index=False):
        if loss_history:
            hist = np.vstack(loss_history[-window:])
            n_hist = len(hist)
            cumulative = hist.sum(axis=0)
            eta = float(np.sqrt(2.0 * np.log(k) / n_hist))
            logits = -eta * cumulative
            logits -= float(np.max(logits))
            weights = np.exp(logits)
            weights /= float(weights.sum())
        else:
            n_hist = 0
            eta = float("nan")
            weights = np.ones(k, dtype=float) / k

        probs = np.array([float(getattr(row, f"{e}_prob")) for e in experts], dtype=float)
        p_router = float(np.dot(weights, probs))
        y = int(row.target)
        pred_rows.append({
            "date": row.date,
            "router_id": router_id,
            "window": window,
            "prob_up": p_router,
            "target": y,
            "same_session_return": float(row.same_session_return),
        })
        wr = {"date": row.date, "router_id": router_id, "window": window, "n_history": n_hist, "eta": eta}
        for i, expert in enumerate(experts):
            wr[f"weight_{expert}"] = float(weights[i])
        weight_rows.append(wr)

        loss_history.append((probs - y) ** 2)

    return pd.DataFrame(pred_rows), pd.DataFrame(weight_rows)


def _metric_row(model_id: str, y: np.ndarray, p: np.ndarray, returns: np.ndarray) -> dict[str, object]:
    m = evaluate_probabilities(y, p, returns)
    return {
        "model_id": model_id,
        "n": int(m.n),
        "log_loss": float(m.log_loss),
        "brier_score": float(m.brier_score),
        "roc_auc": float(m.roc_auc),
        "accuracy": float(m.accuracy),
    }


def run(predictions: pd.DataFrame, *, out_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    df = predictions.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise").dt.normalize()
    df = df.sort_values("date").reset_index(drop=True)
    required = ["date", "target", "same_session_return", *[f"{e}_prob" for e in ALL_EXPERTS]]
    df = df.dropna(subset=required).copy().reset_index(drop=True)
    y = df["target"].astype(int).to_numpy()
    returns = df["same_session_return"].astype(float).to_numpy()

    pred_parts: list[pd.DataFrame] = []
    weight_parts: list[pd.DataFrame] = []
    metric_rows: list[dict[str, object]] = []

    metric_rows.append(_metric_row("baseline", y, df["baseline_prob"].to_numpy(float), returns))
    for expert in ALL_EXPERTS[1:]:
        metric_rows.append(_metric_row(expert, y, df[f"{expert}_prob"].to_numpy(float), returns))

    for label, experts in (("all", ALL_EXPERTS), ("traditional", TRAD_EXPERTS)):
        for window in WINDOWS:
            router_id = f"rolling_hedge_{label}_{window}"
            pred, weights = _run_router(df, experts, window, router_id)
            pred_parts.append(pred)
            weight_parts.append(weights)
            metric_rows.append(_metric_row(router_id, y, pred["prob_up"].to_numpy(float), returns))

    router_predictions = pd.concat(pred_parts, ignore_index=True)
    weights = pd.concat(weight_parts, ignore_index=True)
    metrics = pd.DataFrame(metric_rows).sort_values("log_loss").reset_index(drop=True)

    year_rows: list[dict[str, object]] = []
    for year in sorted(df["date"].dt.year.unique()):
        base_mask = df["date"].dt.year == year
        yy = df.loc[base_mask, "target"].astype(int).to_numpy()
        rr = df.loc[base_mask, "same_session_return"].astype(float).to_numpy()
        year_rows.append({"year": int(year), **_metric_row("baseline", yy, df.loc[base_mask, "baseline_prob"].to_numpy(float), rr)})
        for router_id in sorted(router_predictions["router_id"].unique()):
            rp = router_predictions.loc[(router_predictions["router_id"] == router_id) & (pd.to_datetime(router_predictions["date"]).dt.year == year), "prob_up"].to_numpy(float)
            year_rows.append({"year": int(year), **_metric_row(router_id, yy, rp, rr)})
    year_metrics = pd.DataFrame(year_rows)

    ending_rows: list[dict[str, object]] = []
    for router_id in sorted(weights["router_id"].unique()):
        w = weights.loc[weights["router_id"] == router_id].sort_values("date")
        last = w.iloc[-1]
        for col in [c for c in w.columns if c.startswith("weight_")]:
            ending_rows.append({
                "router_id": router_id,
                "expert": col.replace("weight_", ""),
                "ending_weight": float(last[col]),
                "max_weight": float(w[col].max()),
                "min_weight": float(w[col].min()),
            })
    weight_summary = pd.DataFrame(ending_rows)

    outputs = {
        "metrics": metrics,
        "year_metrics": year_metrics,
        "router_predictions": router_predictions,
        "weights": weights,
        "weight_summary": weight_summary,
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, table in outputs.items():
            table.to_csv(out_dir / f"{name}.csv", index=False)
        (out_dir / "run_metadata.json").write_text(json.dumps({
            "experiment_id": EXPERIMENT_ID,
            "status": "RETROSPECTIVE_TRACK_T",
            "windows": list(WINDOWS),
            "algorithm": "trailing-window Hedge; Brier loss; eta=sqrt(2 ln K / n_history)",
            "sessions": int(len(df)),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lines = [
            f"# {EXPERIMENT_ID} — Rolling-window online routers",
            "",
            "**RETROSPECTIVE / TRACK T ONLY.**",
            "",
            "Every session uses only expert losses realized before that session. Windows 20/60/120 are all reported; none is selected as confirmatory.",
            "",
            "## Full-period metrics",
            "",
            tabulate(metrics, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
            "",
            "## Calendar-year metrics",
            "",
            tabulate(year_metrics, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
            "",
            "## Weight diagnostics",
            "",
            tabulate(weight_summary, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
            "",
            "Interpretation: a rolling router that improves both 2025 and 2026 would support the hypothesis that the expert edge is time-varying and needs forgetting. It remains a trading-utility result, not traditional uniqueness evidence.",
            "",
        ]
        (out_dir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=EXPERIMENT_ID)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(pd.read_csv(args.predictions), out_dir=args.out)
    print((args.out / "SUMMARY.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
