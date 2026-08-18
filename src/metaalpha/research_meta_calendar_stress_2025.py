from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

from .data_sources import DataManifest, fetch_akshare_index
from .hybrid_model import evaluate_probabilities, fit_predict_probability
from .market_baseline import BASE_CATEGORICAL, BASE_CONTINUOUS, TARGET_DIRECTION, TARGET_RETURN
from .meta_branch import META_CANDIDATE_FEATURES, META_NEGATIVE_CONTROL_FEATURES, build_meta_historical_dataset


EXPERIMENT_ID = "META_CALENDAR_STRESS_2025_001"
TEST_START = pd.Timestamp("2025-01-01")
TEST_END = pd.Timestamp("2026-08-17")
CAL_CAT = ["cal_day_of_month", "cal_iso_week", "cal_quarter"]
CAL_CONT = [
    "cal_days_to_month_end",
    "cal_annual_sin_1", "cal_annual_cos_1",
    "cal_annual_sin_2", "cal_annual_cos_2",
    "cal_annual_sin_3", "cal_annual_cos_3",
]
BRANCHES = tuple(META_CANDIDATE_FEATURES) + tuple(META_NEGATIVE_CONTROL_FEATURES)


def _add_rich_calendar(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    d = pd.to_datetime(out["date"], errors="raise").dt.normalize()
    out["cal_day_of_month"] = d.dt.day.astype(int)
    out["cal_iso_week"] = d.dt.isocalendar().week.astype(int)
    out["cal_quarter"] = d.dt.quarter.astype(int)
    month_end = d + pd.offsets.MonthEnd(0)
    out["cal_days_to_month_end"] = (month_end - d).dt.days.astype(float)
    day_of_year = d.dt.dayofyear.astype(float)
    denom = np.where(d.dt.is_leap_year, 366.0, 365.0)
    phase = 2.0 * np.pi * day_of_year / denom
    for k in (1, 2, 3):
        out[f"cal_annual_sin_{k}"] = np.sin(k * phase)
        out[f"cal_annual_cos_{k}"] = np.cos(k * phase)
    return out


def _metric_row(model_id: str, metrics, best_c: float) -> dict[str, object]:
    row = asdict(metrics)
    row.update({"model_id": model_id, "best_C": float(best_c)})
    return row


def run(raw: pd.DataFrame, *, manifest: DataManifest | None = None, out_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    dataset = _add_rich_calendar(build_meta_historical_dataset(raw))
    required = [
        "date", TARGET_DIRECTION, TARGET_RETURN,
        *BASE_CONTINUOUS, *BASE_CATEGORICAL, *CAL_CONT, *CAL_CAT,
    ]
    for cols in META_CANDIDATE_FEATURES.values():
        required.extend(cols)
    for cols in META_NEGATIVE_CONTROL_FEATURES.values():
        required.extend(cols)
    dataset = dataset.dropna(subset=list(dict.fromkeys(required))).copy().sort_values("date").reset_index(drop=True)

    train = dataset.loc[dataset["date"] < TEST_START].copy().reset_index(drop=True)
    test = dataset.loc[(dataset["date"] >= TEST_START) & (dataset["date"] <= TEST_END)].copy().reset_index(drop=True)
    if len(train) < 7000 or len(test) < 300:
        raise ValueError("insufficient train/test rows")

    y = test[TARGET_DIRECTION].astype(int).to_numpy()
    returns = test[TARGET_RETURN].astype(float).to_numpy()
    prediction = pd.DataFrame({
        "date": test["date"].to_numpy(),
        "target": y,
        "same_session_return": returns,
    })
    metric_rows: list[dict[str, object]] = []
    tuning_parts: list[pd.DataFrame] = []

    # Frozen ordinary market baseline.
    p0, c0, t0 = fit_predict_probability(
        train, test,
        numeric_cols=list(BASE_CONTINUOUS),
        categorical_cols=list(BASE_CATEGORICAL),
        target_col=TARGET_DIRECTION,
    )
    m0 = evaluate_probabilities(y, p0, returns)
    prediction["market_baseline_prob"] = p0
    metric_rows.append(_metric_row("market_baseline", m0, c0))
    t0 = t0.copy(); t0.insert(0, "model_id", "market_baseline"); tuning_parts.append(t0)

    # Stronger ordinary calendar baseline.
    rich_num = list(BASE_CONTINUOUS) + CAL_CONT
    rich_cat = list(BASE_CATEGORICAL) + CAL_CAT
    pc, cc, tc = fit_predict_probability(
        train, test,
        numeric_cols=rich_num,
        categorical_cols=rich_cat,
        target_col=TARGET_DIRECTION,
    )
    mc = evaluate_probabilities(y, pc, returns)
    prediction["rich_calendar_prob"] = pc
    metric_rows.append(_metric_row("rich_calendar", mc, cc))
    tc = tc.copy(); tc.insert(0, "model_id", "rich_calendar"); tuning_parts.append(tc)

    comparison_rows: list[dict[str, object]] = []
    for branch in BRANCHES:
        cols = META_CANDIDATE_FEATURES.get(branch, META_NEGATIVE_CONTROL_FEATURES.get(branch))
        p, c, tuning = fit_predict_probability(
            train, test,
            numeric_cols=rich_num,
            categorical_cols=rich_cat + list(cols),
            target_col=TARGET_DIRECTION,
        )
        m = evaluate_probabilities(y, p, returns)
        prediction[f"{branch}_prob"] = p
        metric_rows.append(_metric_row(f"rich_calendar_plus_{branch}", m, c))
        tuning = tuning.copy(); tuning.insert(0, "model_id", f"rich_calendar_plus_{branch}"); tuning_parts.append(tuning)
        comparison_rows.append({
            "branch": branch,
            "negative_control": int(branch in META_NEGATIVE_CONTROL_FEATURES),
            "logloss_improvement_vs_rich_calendar": float(mc.log_loss - m.log_loss),
            "brier_improvement_vs_rich_calendar": float(mc.brier_score - m.brier_score),
            "auc_delta_vs_rich_calendar": float(m.roc_auc - mc.roc_auc),
            "accuracy_delta_vs_rich_calendar": float(m.accuracy - mc.accuracy),
            "best_C": float(c),
        })

    metrics = pd.DataFrame(metric_rows).sort_values("log_loss").reset_index(drop=True)
    comparison = pd.DataFrame(comparison_rows).sort_values("logloss_improvement_vs_rich_calendar", ascending=False).reset_index(drop=True)
    tuning = pd.concat(tuning_parts, ignore_index=True)

    year_rows: list[dict[str, object]] = []
    for year in sorted(test["date"].dt.year.unique()):
        mask = test["date"].dt.year == year
        yy = y[mask.to_numpy()]
        rr = returns[mask.to_numpy()]
        for model_id, col in [
            ("market_baseline", "market_baseline_prob"),
            ("rich_calendar", "rich_calendar_prob"),
            *[(f"rich_calendar_plus_{b}", f"{b}_prob") for b in BRANCHES],
        ]:
            mm = evaluate_probabilities(yy, prediction.loc[mask, col].to_numpy(float), rr)
            year_rows.append({"year": int(year), **_metric_row(model_id, mm, float(metrics.loc[metrics["model_id"] == model_id, "best_C"].iloc[0]))})
    year_metrics = pd.DataFrame(year_rows)

    outputs = {
        "metrics": metrics,
        "comparison_vs_rich_calendar": comparison,
        "year_metrics": year_metrics,
        "predictions": prediction,
        "inner_tuning": tuning,
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, table in outputs.items():
            table.to_csv(out_dir / f"{name}.csv", index=False)
        metadata = {
            "experiment_id": EXPERIMENT_ID,
            "status": "RETROSPECTIVE_DESCRIPTIVE",
            "train_rows": len(train),
            "test_rows": len(test),
            "calendar_categorical": CAL_CAT,
            "calendar_continuous": CAL_CONT,
        }
        (out_dir / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if manifest is not None:
            (out_dir / "data_manifest.json").write_text(manifest.to_json() + "\n", encoding="utf-8")
        lines = [
            f"# {EXPERIMENT_ID} — Rich Gregorian calendar stress test",
            "",
            "**RETROSPECTIVE / DESCRIPTIVE ONLY.**",
            "",
            f"Train rows: **{len(train):,}**; test rows: **{len(test):,}** ({test['date'].min().date()} .. {test['date'].max().date()}).",
            "All calendar controls are deterministic from the target civil date and known before 09:25.",
            "",
            "## Full-period metrics",
            "",
            tabulate(metrics[["model_id", "n", "log_loss", "brier_score", "roc_auc", "accuracy", "best_C"]], headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
            "",
            "## Increment beyond rich Gregorian calendar baseline",
            "",
            tabulate(comparison, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
            "",
            "## Calendar-year metrics",
            "",
            tabulate(year_metrics[["year", "model_id", "n", "log_loss", "brier_score", "roc_auc", "accuracy"]], headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
            "",
            "Interpretation: if symbolic/hash gains shrink materially versus the richer ordinary-calendar baseline, earlier gains are compatible with generic calendar partitioning. Persistence of a traditional gain still does not establish uniqueness without matched-null tests.",
            "",
        ]
        (out_dir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=EXPERIMENT_ID)
    parser.add_argument("--provider", default="sina")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--raw-start", default="19901219")
    parser.add_argument("--end", default="20260817")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw, manifest = fetch_akshare_index(
        symbol=args.symbol,
        start_date=args.raw_start,
        end_date=args.end,
        provider=args.provider,
    )
    run(raw, manifest=manifest, out_dir=args.out)
    print((args.out / "SUMMARY.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
