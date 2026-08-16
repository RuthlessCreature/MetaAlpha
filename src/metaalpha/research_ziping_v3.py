from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .data_sources import DataManifest, fetch_akshare_index
from .pipeline import build_dataset
from .validation import benjamini_hochberg


HYPOTHESIS_ID = "ZIPING_V3_001"
TARGET = "ret_fwd_1"
BASE_USE_FEATURE = "zpzt_use__v2__selected_ten_god"
CALENDAR_FEATURES = ("calendar__v1__weekday", "calendar__v1__month")
ROUTE_FEATURES = (
    "zpzt_route__v3__route_state",
    "zpzt_route__v3__route_hit_count",
    "zpzt_route__v3__route_unresolved_count",
    "zpzt_route__v3__assistant_count",
    "zpzt_route__v3__source_example_rescue_hit_count",
    "zpzt_route__v3__requires_strength_route_count",
    "zpzt_route__v3__requires_position_route_count",
    "zpzt_route__v3__requires_quantity_route_count",
    "zpzt_route__v3__visible_combination_pair_count",
)
SHIFT_SESSIONS = (17, 31, 47)
HAC_MAXLAGS = 5
MIN_LEVEL_N = 100
MIN_ROWS = 500

ERAS = (
    ("history_all", None, "2026-08-14"),
    ("era_1990_2004", None, "2004-12-31"),
    ("era_2005_2014", "2005-01-01", "2014-12-31"),
    ("era_2015_2020", "2015-01-01", "2020-12-31"),
    ("era_2021_2026", "2021-01-01", "2026-08-14"),
)


def _slice_and_purge(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    dates = pd.to_datetime(df["date"], errors="raise")
    mask = pd.Series(True, index=df.index)
    if start is not None:
        mask &= dates >= pd.Timestamp(start)
    if end is not None:
        mask &= dates <= pd.Timestamp(end)
    part = df.loc[mask].copy().sort_values("date").reset_index(drop=True)
    return part.iloc[:-1].copy() if len(part) > 1 else part.iloc[:0].copy()


def _collapse_rare(series: pd.Series, min_n: int) -> pd.Series:
    values = series.astype(str)
    counts = values.value_counts(dropna=False)
    rare = set(counts[counts < min_n].index.astype(str))
    return values.map(lambda x: "__RARE__" if x in rare else x)


def _dummy_block(df: pd.DataFrame, columns: tuple[str, ...], prefix: str) -> pd.DataFrame:
    cat = df[list(columns)].astype(str)
    return pd.get_dummies(cat, prefix=[f"{prefix}{i}" for i in range(len(columns))], drop_first=True, dtype=float)


def _joint_route_test(
    df: pd.DataFrame,
    feature: str,
    *,
    min_level_n: int,
    min_rows: int,
    maxlags: int,
) -> tuple[dict[str, object] | None, pd.DataFrame]:
    needed = ["date", TARGET, BASE_USE_FEATURE, *CALENDAR_FEATURES, feature]
    base = df[needed].dropna().copy().sort_values("date").reset_index(drop=True)
    if len(base) < min_rows:
        return None, pd.DataFrame()

    base[feature] = _collapse_rare(base[feature], min_level_n)
    if base[feature].nunique() < 2:
        return None, pd.DataFrame()

    baseline_cols = (BASE_USE_FEATURE, *CALENDAR_FEATURES)
    baseline_dummies = _dummy_block(base, baseline_cols, "base__")
    route_dummies = pd.get_dummies(
        base[feature].astype(str),
        prefix="route",
        drop_first=True,
        dtype=float,
    )
    if route_dummies.shape[1] == 0:
        return None, pd.DataFrame()

    x_base = sm.add_constant(baseline_dummies, prepend=True, has_constant="add")
    x_full = sm.add_constant(
        pd.concat([baseline_dummies, route_dummies], axis=1),
        prepend=True,
        has_constant="add",
    )
    y = base[TARGET].to_numpy(dtype=float)

    fit_base = sm.OLS(y, x_base).fit()
    fit = sm.OLS(y, x_full).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": int(maxlags), "use_correction": True},
    )

    route_cols = list(route_dummies.columns)
    parameter_names = list(x_full.columns)
    restriction = np.zeros((len(route_cols), len(parameter_names)), dtype=float)
    for row_idx, col in enumerate(route_cols):
        restriction[row_idx, parameter_names.index(col)] = 1.0
    wald = fit.wald_test(restriction, scalar=True)

    coef_rows: list[dict[str, object]] = []
    for col in route_cols:
        coef_rows.append(
            {
                "feature": feature,
                "dummy": col,
                "coefficient": float(fit.params[col]),
                "coefficient_bps": float(fit.params[col]) * 10000.0,
                "t_stat": float(fit.tvalues[col]),
                "p_value": float(fit.pvalues[col]),
            }
        )
    coef_df = pd.DataFrame(coef_rows)

    row = {
        "feature": feature,
        "n": int(len(base)),
        "levels_after_rare_collapse": int(base[feature].nunique()),
        "route_dummy_count": int(len(route_cols)),
        "wald_stat": float(np.asarray(wald.statistic).squeeze()),
        "p_value": float(np.asarray(wald.pvalue).squeeze()),
        "delta_r2": float(fit.rsquared - fit_base.rsquared),
        "full_r2": float(fit.rsquared),
        "max_abs_route_beta_bps": float(coef_df["coefficient_bps"].abs().max()),
        "design_rank": int(np.linalg.matrix_rank(x_full.to_numpy(dtype=float))),
        "design_columns": int(x_full.shape[1]),
        "rank_deficient": int(np.linalg.matrix_rank(x_full.to_numpy(dtype=float)) < x_full.shape[1]),
        "inference": "ols_hac_joint_wald",
        "hac_maxlags": int(maxlags),
    }
    return row, coef_df


def _run_era(
    part: pd.DataFrame,
    *,
    era: str,
    min_level_n: int,
    min_rows: int,
) -> tuple[list[dict[str, object]], list[pd.DataFrame]]:
    rows: list[dict[str, object]] = []
    coefficients: list[pd.DataFrame] = []

    for feature in ROUTE_FEATURES:
        row, coef = _joint_route_test(
            part,
            feature,
            min_level_n=min_level_n,
            min_rows=min_rows,
            maxlags=HAC_MAXLAGS,
        )
        if row is not None:
            row.update({"era": era, "test_kind": "registered", "shift_sessions": 0})
            rows.append(row)
            if not coef.empty:
                coef.insert(0, "era", era)
                coef.insert(1, "test_kind", "registered")
                coef.insert(2, "shift_sessions", 0)
                coefficients.append(coef)

        for shift in SHIFT_SESSIONS:
            shifted_feature = f"__shift_{shift}__{feature}"
            shifted = part.copy()
            shifted[shifted_feature] = shifted[feature].shift(shift)
            null_row, null_coef = _joint_route_test(
                shifted,
                shifted_feature,
                min_level_n=min_level_n,
                min_rows=min_rows,
                maxlags=HAC_MAXLAGS,
            )
            if null_row is None:
                continue
            null_row["source_feature"] = feature
            null_row.update({"era": era, "test_kind": "shift_null", "shift_sessions": shift})
            rows.append(null_row)
            if not null_coef.empty:
                null_coef.insert(0, "era", era)
                null_coef.insert(1, "test_kind", "shift_null")
                null_coef.insert(2, "shift_sessions", shift)
                null_coef["source_feature"] = feature
                coefficients.append(null_coef)

    return rows, coefficients


def _apply_family_fdr(joint: pd.DataFrame) -> pd.DataFrame:
    if joint.empty:
        return joint
    out = joint.copy()
    out["p_fdr_bh_family"] = np.nan
    for (era, kind), idx in out.groupby(["era", "test_kind"]).groups.items():
        loc = list(idx)
        out.loc[loc, "p_fdr_bh_family"] = benjamini_hochberg(out.loc[loc, "p_value"])
    return out.sort_values(["era", "test_kind", "p_fdr_bh_family", "p_value"]).reset_index(drop=True)


def _diagnostics(joint: pd.DataFrame) -> pd.DataFrame:
    if joint.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for keys, g in joint.groupby(["era", "test_kind"], dropna=False):
        rows.append(
            {
                "era": keys[0],
                "test_kind": keys[1],
                "tests": int(len(g)),
                "min_family_fdr": float(g["p_fdr_bh_family"].min()),
                "max_delta_r2": float(g["delta_r2"].max()),
                "max_abs_route_beta_bps": float(g["max_abs_route_beta_bps"].max()),
                "rank_deficient_tests": int(g["rank_deficient"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["era", "test_kind"]).reset_index(drop=True)


def run_ziping_v3_exploration(
    raw: pd.DataFrame,
    *,
    out_dir: Path,
    manifest: DataManifest | None = None,
    min_level_n: int = MIN_LEVEL_N,
    min_rows: int = MIN_ROWS,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    dataset = build_dataset(raw, include_ziping=True)
    dataset.to_csv(out_dir / "dataset_ziping_v3.csv", index=False)

    joint_rows: list[dict[str, object]] = []
    coefficient_parts: list[pd.DataFrame] = []
    era_rows: list[dict[str, object]] = []

    for era, start, end in ERAS:
        part = _slice_and_purge(dataset, start, end)
        era_rows.append(
            {
                "era": era,
                "start": start,
                "end": end,
                "rows_after_purge": int(len(part)),
            }
        )
        rows, coefs = _run_era(
            part,
            era=era,
            min_level_n=min_level_n,
            min_rows=min_rows,
        )
        joint_rows.extend(rows)
        coefficient_parts.extend(coefs)

    joint = _apply_family_fdr(pd.DataFrame(joint_rows))
    coefficients = pd.concat(coefficient_parts, ignore_index=True) if coefficient_parts else pd.DataFrame()
    diagnostics = _diagnostics(joint)
    eras = pd.DataFrame(era_rows)

    joint.to_csv(out_dir / "incremental_joint_tests.csv", index=False)
    coefficients.to_csv(out_dir / "route_level_coefficients.csv", index=False)
    diagnostics.to_csv(out_dir / "diagnostic_summary.csv", index=False)
    eras.to_csv(out_dir / "era_boundaries.csv", index=False)

    if manifest is not None:
        (out_dir / "data_manifest.json").write_text(manifest.to_json() + "\n", encoding="utf-8")

    metadata = {
        "hypothesis_id": HYPOTHESIS_ID,
        "status": "EXPLORATORY_ONLY_NO_UNSEEN_HISTORY",
        "historical_last_date": "2026-08-14",
        "target": TARGET,
        "baseline_covariates": [BASE_USE_FEATURE, *CALENDAR_FEATURES],
        "route_features": list(ROUTE_FEATURES),
        "rare_level_min_n": min_level_n,
        "minimum_rows": min_rows,
        "hac_maxlags": HAC_MAXLAGS,
        "shift_null_sessions": list(SHIFT_SESSIONS),
        "provider_required": "sina",
        "aggregate_score_defined": False,
    }
    (out_dir / "run_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# ZIPING_V3_001 — Incremental Assistant/Route Graph Exploration",
        "",
        "**Evidence status: EXPLORATORY ONLY. Historical data are not an unseen holdout.**",
        "",
        "Primary question: after controlling for the v2 selected-use ten god plus Gregorian weekday/month fixed effects, do v3 相神/route states add incremental next-session-return information?",
        "",
        "Each registered route feature is tested as a categorical dummy block using a HAC joint Wald test. BH-FDR is applied across all registered route features within each era. The same procedure is repeated for 17/31/47-session shifted controls.",
        "",
        "## Diagnostic minima",
        "",
    ]
    if diagnostics.empty:
        lines.append("No eligible joint tests.")
    else:
        lines.append(diagnostics.to_markdown(index=False))
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "Historical interest requires the same registered route feature to survive family correction in at least two of 2005-2014, 2015-2020 and 2021-2026, while not being materially weaker than its shifted controls. Any future rule would still require a separately frozen forward-only registration.",
        ]
    )
    (out_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "dataset": dataset,
        "joint": joint,
        "coefficients": coefficients,
        "diagnostics": diagnostics,
        "eras": eras,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ZIPING_V3_001 incremental route-graph exploration")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--fetch-akshare", action="store_true")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--start", default="19901219")
    parser.add_argument("--end", default="20260814")
    parser.add_argument("--provider", default="sina", choices=("sina",))
    parser.add_argument("--out", type=Path, default=Path("reports/sse_ziping_v3_exploratory"))
    parser.add_argument("--min-level-n", type=int, default=MIN_LEVEL_N)
    parser.add_argument("--min-rows", type=int, default=MIN_ROWS)
    args = parser.parse_args()

    manifest: DataManifest | None = None
    if args.fetch_akshare:
        raw, manifest = fetch_akshare_index(
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
            provider=args.provider,
        )
    else:
        raw = pd.read_csv(args.input)

    result = run_ziping_v3_exploration(
        raw,
        out_dir=args.out,
        manifest=manifest,
        min_level_n=args.min_level_n,
        min_rows=args.min_rows,
    )
    print(f"rows={len(result['dataset'])}")
    print(f"joint_tests={len(result['joint'])}")
    print(f"report={args.out / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
