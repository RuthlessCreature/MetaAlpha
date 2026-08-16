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


HYPOTHESIS_ID = "ZIPING_V4_001"
TARGET = "ret_fwd_1"
BASELINE_FEATURES = (
    "zpzt_use__v2__selected_ten_god",
    "zpzt_route__v3__route_state",
    "calendar__v1__weekday",
    "calendar__v1__month",
)
FEATURES = (
    "zpzt_structure__v4__wealth_resource_position_resolution",
    "zpzt_structure__v4__selected_use_root_bin",
    "zpzt_structure__v4__selected_use_root_month",
    "zpzt_structure__v4__assistant_rooted_stem_count",
    "zpzt_structure__v4__assistant_all_visible_rooted",
    "zpzt_structure__v4__daymaster_root_bin",
    "zpzt_structure__v4__daymaster_root_month",
    "zpzt_structure__v4__visible_support_balance",
    "zpzt_structure__v4__support_profile",
    "zpzt_route__v4__route_state",
    "zpzt_route__v4__resolved_from_position_count",
    "zpzt_route__v4__route_blocked_count",
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


def _invalid_joint_row(
    *,
    feature: str,
    n: int,
    levels: int,
    feature_dummy_count: int,
    design_rank: int,
    design_columns: int,
    constraint_cov_rank: int,
    invalid_reason: str,
) -> dict[str, object]:
    return {
        "feature": feature,
        "n": int(n),
        "levels_after_rare_collapse": int(levels),
        "feature_dummy_count": int(feature_dummy_count),
        "wald_stat": np.nan,
        "p_value": np.nan,
        "delta_r2": np.nan,
        "full_r2": np.nan,
        "max_abs_beta_bps": np.nan,
        "design_rank": int(design_rank),
        "design_columns": int(design_columns),
        "rank_deficient": int(design_rank < design_columns),
        "constraint_cov_rank": int(constraint_cov_rank),
        "constraint_count": int(feature_dummy_count),
        "valid_inference": 0,
        "invalid_reason": invalid_reason,
        "inference": "INVALID_OLS_HAC_JOINT_WALD",
        "hac_maxlags": HAC_MAXLAGS,
    }


def _joint_feature_test(
    df: pd.DataFrame,
    feature: str,
    *,
    min_level_n: int,
    min_rows: int,
    maxlags: int,
) -> tuple[dict[str, object] | None, pd.DataFrame]:
    """Run one incremental categorical block test with explicit identifiability QC.

    A joint test is inferentially valid only when both conditions hold:

    1. the complete OLS design matrix is full column rank;
    2. the HAC covariance submatrix for the tested feature-dummy block is full rank.

    Invalid tests are retained in the audit table with ``p_value=NaN`` and are
    excluded from BH-FDR. This prevents structural collinearity or singular HAC
    restrictions from producing meaningless coefficients/p-values.
    """
    needed = ["date", TARGET, *BASELINE_FEATURES, feature]
    base = df[needed].dropna().copy().sort_values("date").reset_index(drop=True)
    if len(base) < min_rows:
        return None, pd.DataFrame()

    for baseline in BASELINE_FEATURES:
        base[baseline] = base[baseline].astype(str)
    base[feature] = _collapse_rare(base[feature], min_level_n)
    if base[feature].nunique() < 2:
        return None, pd.DataFrame()

    baseline_dummies = pd.get_dummies(
        base[list(BASELINE_FEATURES)],
        prefix=[f"base__{i}" for i in range(len(BASELINE_FEATURES))],
        drop_first=True,
        dtype=float,
    )
    feature_dummies = pd.get_dummies(
        base[feature].astype(str),
        prefix="v4",
        drop_first=True,
        dtype=float,
    )
    if feature_dummies.shape[1] == 0:
        return None, pd.DataFrame()

    x_base = sm.add_constant(baseline_dummies, prepend=True, has_constant="add")
    x_full = sm.add_constant(
        pd.concat([baseline_dummies, feature_dummies], axis=1),
        prepend=True,
        has_constant="add",
    )
    y = base[TARGET].to_numpy(dtype=float)

    feature_cols = list(feature_dummies.columns)
    design_array = x_full.to_numpy(dtype=float)
    design_rank = int(np.linalg.matrix_rank(design_array))
    design_columns = int(x_full.shape[1])
    if design_rank < design_columns:
        row = _invalid_joint_row(
            feature=feature,
            n=len(base),
            levels=base[feature].nunique(),
            feature_dummy_count=len(feature_cols),
            design_rank=design_rank,
            design_columns=design_columns,
            constraint_cov_rank=0,
            invalid_reason="design_matrix_rank_deficient",
        )
        return row, pd.DataFrame()

    fit_base = sm.OLS(y, x_base).fit()
    fit = sm.OLS(y, x_full).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": int(maxlags), "use_correction": True},
    )

    cov = fit.cov_params()
    feature_cov = cov.loc[feature_cols, feature_cols].to_numpy(dtype=float)
    constraint_cov_rank = int(np.linalg.matrix_rank(feature_cov))
    if constraint_cov_rank < len(feature_cols):
        row = _invalid_joint_row(
            feature=feature,
            n=len(base),
            levels=base[feature].nunique(),
            feature_dummy_count=len(feature_cols),
            design_rank=design_rank,
            design_columns=design_columns,
            constraint_cov_rank=constraint_cov_rank,
            invalid_reason="hac_constraint_covariance_rank_deficient",
        )
        return row, pd.DataFrame()

    parameter_names = list(x_full.columns)
    restriction = np.zeros((len(feature_cols), len(parameter_names)), dtype=float)
    for row_idx, col in enumerate(feature_cols):
        restriction[row_idx, parameter_names.index(col)] = 1.0
    wald = fit.wald_test(restriction, scalar=True)

    coef_rows = [
        {
            "feature": feature,
            "dummy": col,
            "coefficient": float(fit.params[col]),
            "coefficient_bps": float(fit.params[col]) * 10000.0,
            "t_stat": float(fit.tvalues[col]),
            "p_value": float(fit.pvalues[col]),
            "valid_inference": 1,
        }
        for col in feature_cols
    ]
    coef_df = pd.DataFrame(coef_rows)

    row = {
        "feature": feature,
        "n": int(len(base)),
        "levels_after_rare_collapse": int(base[feature].nunique()),
        "feature_dummy_count": int(len(feature_cols)),
        "wald_stat": float(np.asarray(wald.statistic).squeeze()),
        "p_value": float(np.asarray(wald.pvalue).squeeze()),
        "delta_r2": float(fit.rsquared - fit_base.rsquared),
        "full_r2": float(fit.rsquared),
        "max_abs_beta_bps": float(coef_df["coefficient_bps"].abs().max()),
        "design_rank": design_rank,
        "design_columns": design_columns,
        "rank_deficient": 0,
        "constraint_cov_rank": constraint_cov_rank,
        "constraint_count": int(len(feature_cols)),
        "valid_inference": 1,
        "invalid_reason": "",
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

    for feature in FEATURES:
        row, coef = _joint_feature_test(
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
            shifted_name = f"__shift_{shift}__{feature}"
            shifted = part.copy()
            shifted[shifted_name] = shifted[feature].shift(shift)
            null_row, null_coef = _joint_feature_test(
                shifted,
                shifted_name,
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


def _apply_fdr(joint: pd.DataFrame) -> pd.DataFrame:
    if joint.empty:
        return joint
    out = joint.copy()
    out["p_fdr_bh_family"] = np.nan
    for _, idx in out.groupby(["era", "test_kind"]).groups.items():
        loc = list(idx)
        valid_loc = [
            i for i in loc
            if int(out.at[i, "valid_inference"]) == 1 and np.isfinite(out.at[i, "p_value"])
        ]
        if not valid_loc:
            continue
        out.loc[valid_loc, "p_fdr_bh_family"] = benjamini_hochberg(
            out.loc[valid_loc, "p_value"]
        )
    return out.sort_values(
        ["era", "test_kind", "valid_inference", "p_fdr_bh_family", "p_value"],
        ascending=[True, True, False, True, True],
        na_position="last",
    ).reset_index(drop=True)


def _diagnostics(joint: pd.DataFrame) -> pd.DataFrame:
    if joint.empty:
        return pd.DataFrame()
    rows = []
    for keys, g in joint.groupby(["era", "test_kind"], dropna=False):
        valid = g.loc[g["valid_inference"] == 1].copy()
        rows.append(
            {
                "era": keys[0],
                "test_kind": keys[1],
                "tests_total": int(len(g)),
                "valid_tests": int(len(valid)),
                "invalid_tests": int(len(g) - len(valid)),
                "min_family_fdr": float(valid["p_fdr_bh_family"].min()) if not valid.empty else np.nan,
                "max_delta_r2": float(valid["delta_r2"].max()) if not valid.empty else np.nan,
                "max_abs_beta_bps": float(valid["max_abs_beta_bps"].max()) if not valid.empty else np.nan,
                "design_rank_deficient_tests": int((g["invalid_reason"] == "design_matrix_rank_deficient").sum()),
                "hac_constraint_rank_deficient_tests": int((g["invalid_reason"] == "hac_constraint_covariance_rank_deficient").sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["era", "test_kind"]).reset_index(drop=True)


def run_ziping_v4_exploration(
    raw: pd.DataFrame,
    *,
    out_dir: Path,
    manifest: DataManifest | None = None,
    min_level_n: int = MIN_LEVEL_N,
    min_rows: int = MIN_ROWS,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    dataset = build_dataset(raw, include_ziping=True)
    dataset.to_csv(out_dir / "dataset_ziping_v4.csv", index=False)

    rows: list[dict[str, object]] = []
    coef_parts: list[pd.DataFrame] = []
    era_rows: list[dict[str, object]] = []

    for era, start, end in ERAS:
        part = _slice_and_purge(dataset, start, end)
        era_rows.append({"era": era, "start": start, "end": end, "rows_after_purge": int(len(part))})
        era_result, era_coefs = _run_era(part, era=era, min_level_n=min_level_n, min_rows=min_rows)
        rows.extend(era_result)
        coef_parts.extend(era_coefs)

    joint = _apply_fdr(pd.DataFrame(rows))
    coefficients = pd.concat(coef_parts, ignore_index=True) if coef_parts else pd.DataFrame()
    diagnostics = _diagnostics(joint)
    eras = pd.DataFrame(era_rows)

    joint.to_csv(out_dir / "incremental_joint_tests.csv", index=False)
    coefficients.to_csv(out_dir / "feature_level_coefficients.csv", index=False)
    diagnostics.to_csv(out_dir / "diagnostic_summary.csv", index=False)
    eras.to_csv(out_dir / "era_boundaries.csv", index=False)

    invalid = joint.loc[joint["valid_inference"] == 0].copy()
    invalid.to_csv(out_dir / "invalid_inference_tests.csv", index=False)

    if manifest is not None:
        (out_dir / "data_manifest.json").write_text(manifest.to_json() + "\n", encoding="utf-8")

    metadata = {
        "hypothesis_id": HYPOTHESIS_ID,
        "status": "CORRECTED_EXPLORATORY_REANALYSIS_AFTER_INFERENCE_QC",
        "historical_last_date": "2026-08-14",
        "target": TARGET,
        "baseline_covariates": list(BASELINE_FEATURES),
        "features": list(FEATURES),
        "rare_level_min_n": min_level_n,
        "minimum_rows": min_rows,
        "hac_maxlags": HAC_MAXLAGS,
        "shift_null_sessions": list(SHIFT_SESSIONS),
        "provider_required": "sina",
        "strength_score_defined": False,
        "fortune_score_defined": False,
        "supersedes_run_for_inference": "31946158306",
        "superseded_run_status": "INVALIDATED_FOR_INFERENCE_QC",
        "qc_corrections": [
            "joint tests require a full-rank complete design matrix",
            "HAC covariance submatrix for the tested dummy block must be full rank",
            "invalid tests retain an audit row with p_value=NaN and are excluded from BH-FDR",
            "invalid coefficients are not emitted into the coefficient table or diagnostic maxima",
        ],
    }
    (out_dir / "run_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# ZIPING_V4_001 — Corrected Structural Predicate Historical Exploration",
        "",
        "**Evidence status: CORRECTED EXPLORATORY REANALYSIS. Historical observations are not an unseen holdout.**",
        "",
        "The first v4 run (31946158306) is invalidated for inferential use because at least one registered joint test used a rank-deficient design / singular restriction covariance. This corrected run preserves the registered feature definitions and baseline, but excludes mathematically unidentified tests from BH-FDR.",
        "",
        "The frozen baseline includes v2 selected-use ten-god fixed effects, v3 route-state fixed effects, Gregorian weekday fixed effects and Gregorian month fixed effects.",
        "",
        "V4 tests whether source-constrained position/root/support predicates add incremental next-session-return information. No numeric strong/weak or fortune score is defined.",
        "",
        "## Diagnostic minima",
        "",
    ]
    if diagnostics.empty:
        lines.append("No eligible tests.")
    else:
        lines.append(diagnostics.to_markdown(index=False))
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "Historical interest requires the same valid registered v4 feature to survive family correction in at least two of 2005-2014, 2015-2020 and 2021-2026, while not being materially weaker than its 17/31/47-session shifted controls. Promotion would still require a separately frozen future-only experiment.",
        ]
    )
    (out_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "dataset": dataset,
        "joint": joint,
        "coefficients": coefficients,
        "diagnostics": diagnostics,
        "invalid": invalid,
        "eras": eras,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ZIPING_V4_001 structural-predicate exploration")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--fetch-akshare", action="store_true")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--start", default="19901219")
    parser.add_argument("--end", default="20260814")
    parser.add_argument("--provider", default="sina", choices=("sina",))
    parser.add_argument("--out", type=Path, default=Path("reports/sse_ziping_v4_exploratory"))
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

    result = run_ziping_v4_exploration(
        raw,
        out_dir=args.out,
        manifest=manifest,
        min_level_n=args.min_level_n,
        min_rows=args.min_rows,
    )
    print(f"rows={len(result['dataset'])}")
    print(f"joint_tests={len(result['joint'])}")
    print(f"invalid_tests={len(result['invalid'])}")
    print(f"report={args.out / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
