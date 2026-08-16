from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .calendar_cycle import add_calendar_cycle_features
from .data_sources import DataManifest, fetch_akshare_index
from .labels import add_forward_labels
from .validation import benjamini_hochberg


HYPOTHESIS_ID = "GANZHI_VOL_001"
TARGET = "log_vol_fwd_5"
RAW_TARGET = "vol_fwd_5"
HAC_MAXLAGS = 20
NONOVERLAP_HAC_MAXLAGS = 4
MIN_LEVEL_N = 20
MIN_ROWS = 500
SHIFT_SESSIONS = (17, 31, 47)

BASELINE_CONTINUOUS = (
    "log_vol_back_5_lag1",
    "log_vol_back_20_lag1",
    "abs_ret_1_lag1",
    "normalized_time",
    "normalized_time_squared",
)
BASELINE_CATEGORICAL = (
    "calendar_weekday",
    "calendar_month",
)

ERAS = (
    ("history_all", None, "2026-08-14"),
    ("era_1990_2004", None, "2004-12-31"),
    ("era_2005_2014", "2005-01-01", "2014-12-31"),
    ("era_2015_2020", "2015-01-01", "2020-12-31"),
    ("era_2021_2026", "2021-01-01", "2026-08-14"),
)
LATER_ERAS = ("era_2005_2014", "era_2015_2020", "era_2021_2026")


@dataclass(frozen=True)
class BlockSpec:
    id: str
    kind: str
    columns: tuple[str, ...]


BLOCKS = (
    BlockSpec("solar_term_24", "categorical", ("cycle__v1__prev_jieqi",)),
    BlockSpec("solar_term_phase_quartile", "categorical", ("cycle__v1__jieqi_phase_quartile",)),
    BlockSpec("solar_term_smooth", "continuous_joint", ("cycle__v1__term_phase_sin", "cycle__v1__term_phase_cos")),
    BlockSpec("day_pillar_60", "categorical", ("cycle__v1__day_pillar",)),
    BlockSpec("day_stem_10", "categorical", ("cycle__v1__day_stem",)),
    BlockSpec("day_branch_12", "categorical", ("cycle__v1__day_branch",)),
    BlockSpec("month_stem_10", "categorical", ("cycle__v1__month_stem",)),
    BlockSpec("month_branch_12", "categorical", ("cycle__v1__month_branch",)),
    BlockSpec("jie_or_qi", "categorical", ("cycle__v1__jie_or_qi",)),
)


def _build_dataset(raw: pd.DataFrame) -> pd.DataFrame:
    if not {"date", "close"}.issubset(raw.columns):
        raise ValueError("raw data requires date and close")
    out = raw.copy().sort_values("date").reset_index(drop=True)
    if "symbol" not in out.columns:
        out["symbol"] = "INDEX_000001"
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.normalize()
    out["session_index"] = np.arange(len(out), dtype=int)

    out = add_forward_labels(out)
    out = add_calendar_cycle_features(out)

    # Baselines known no later than t-1 close. The current session's close and
    # return are deliberately excluded from the 09:25 feature baseline.
    prev_ret = out["ret_1"].shift(1)
    out["vol_back_5_lag1"] = prev_ret.rolling(5, min_periods=5).std()
    out["vol_back_20_lag1"] = prev_ret.rolling(20, min_periods=20).std()
    out["log_vol_back_5_lag1"] = np.log(out["vol_back_5_lag1"].where(out["vol_back_5_lag1"] > 0))
    out["log_vol_back_20_lag1"] = np.log(out["vol_back_20_lag1"].where(out["vol_back_20_lag1"] > 0))
    out["abs_ret_1_lag1"] = prev_ret.abs()
    out[TARGET] = np.log(out[RAW_TARGET].where(out[RAW_TARGET] > 0))

    denom = max(len(out) - 1, 1)
    out["normalized_time"] = out["session_index"] / float(denom)
    out["normalized_time_squared"] = out["normalized_time"] ** 2
    out["calendar_weekday"] = out["date"].dt.weekday.astype(str)
    out["calendar_month"] = out["date"].dt.month.astype(str)

    # Shift complete registered blocks on the full session timeline before era
    # slicing, so a 17-session control always means 17 actual dataset sessions.
    for block in BLOCKS:
        for shift in SHIFT_SESSIONS:
            for col in block.columns:
                out[f"control_shift_{shift}__{col}"] = out[col].shift(shift)
    return out


def _slice_and_purge(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    dates = pd.to_datetime(df["date"], errors="raise")
    mask = pd.Series(True, index=df.index)
    if start is not None:
        mask &= dates >= pd.Timestamp(start)
    if end is not None:
        mask &= dates <= pd.Timestamp(end)
    part = df.loc[mask].copy().sort_values("date").reset_index(drop=True)
    # vol_fwd_5 uses t+1..t+5. Purging prevents the target from crossing the
    # descriptive era boundary after labels were computed on the full history.
    return part.iloc[:-5].copy() if len(part) > 5 else part.iloc[:0].copy()


def _collapse_rare(series: pd.Series, min_n: int) -> pd.Series:
    values = series.astype(str)
    counts = values.value_counts(dropna=False)
    rare = set(counts[counts < min_n].index.astype(str))
    return values.map(lambda x: "__RARE__" if x in rare else x)


def _baseline_design(base: pd.DataFrame) -> pd.DataFrame:
    continuous = base[list(BASELINE_CONTINUOUS)].astype(float).reset_index(drop=True)
    categorical = pd.get_dummies(
        base[list(BASELINE_CATEGORICAL)].astype(str),
        prefix=["weekday", "month"],
        drop_first=True,
        dtype=float,
    ).reset_index(drop=True)
    return pd.concat([continuous, categorical], axis=1)


def _block_design(
    base: pd.DataFrame,
    block: BlockSpec,
    *,
    columns: tuple[str, ...],
    min_level_n: int,
) -> pd.DataFrame:
    if block.kind == "continuous_joint":
        return base[list(columns)].astype(float).reset_index(drop=True)
    if block.kind != "categorical":
        raise ValueError(f"unknown block kind: {block.kind}")

    if len(columns) == 1:
        values = _collapse_rare(base[columns[0]], min_level_n)
    else:
        values = base[list(columns)].astype(str).agg("|".join, axis=1)
        values = _collapse_rare(values, min_level_n)
    return pd.get_dummies(values, prefix="block", drop_first=True, dtype=float).reset_index(drop=True)


def _invalid_row(
    block: BlockSpec,
    *,
    n: int,
    block_columns: int,
    design_rank: int,
    design_columns: int,
    constraint_cov_rank: int,
    reason: str,
) -> dict[str, object]:
    return {
        "block_id": block.id,
        "block_kind": block.kind,
        "n": int(n),
        "block_coefficient_count": int(block_columns),
        "wald_stat": np.nan,
        "p_value": np.nan,
        "delta_r2": np.nan,
        "full_r2": np.nan,
        "max_abs_beta": np.nan,
        "design_rank": int(design_rank),
        "design_columns": int(design_columns),
        "constraint_cov_rank": int(constraint_cov_rank),
        "constraint_count": int(block_columns),
        "valid_inference": 0,
        "invalid_reason": reason,
        "inference": "INVALID_OLS_HAC_JOINT_WALD",
    }


def _fit_block(
    df: pd.DataFrame,
    block: BlockSpec,
    *,
    columns: tuple[str, ...] | None = None,
    min_level_n: int = MIN_LEVEL_N,
    min_rows: int = MIN_ROWS,
    hac_maxlags: int = HAC_MAXLAGS,
) -> tuple[dict[str, object] | None, pd.DataFrame]:
    columns = block.columns if columns is None else columns
    needed = ["date", TARGET, *BASELINE_CONTINUOUS, *BASELINE_CATEGORICAL, *columns]
    base = df[needed].dropna().copy().sort_values("date").reset_index(drop=True)
    if len(base) < min_rows:
        return None, pd.DataFrame()

    x_base_raw = _baseline_design(base)
    x_block_raw = _block_design(base, block, columns=columns, min_level_n=min_level_n)
    if x_block_raw.shape[1] == 0:
        return None, pd.DataFrame()

    # Prefix block columns uniquely so continuous block columns cannot collide
    # with baseline column names in the combined design.
    x_block_raw = x_block_raw.copy()
    x_block_raw.columns = [f"tested__{block.id}__{i}" for i in range(x_block_raw.shape[1])]
    block_cols = list(x_block_raw.columns)

    x_base = sm.add_constant(x_base_raw, prepend=True, has_constant="add")
    x_full = sm.add_constant(pd.concat([x_base_raw, x_block_raw], axis=1), prepend=True, has_constant="add")
    y = base[TARGET].to_numpy(dtype=float)

    design_array = x_full.to_numpy(dtype=float)
    design_rank = int(np.linalg.matrix_rank(design_array))
    design_columns = int(x_full.shape[1])
    if design_rank < design_columns:
        return _invalid_row(
            block,
            n=len(base),
            block_columns=len(block_cols),
            design_rank=design_rank,
            design_columns=design_columns,
            constraint_cov_rank=0,
            reason="design_matrix_rank_deficient",
        ), pd.DataFrame()

    fit_base = sm.OLS(y, x_base).fit()
    fit = sm.OLS(y, x_full).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": int(hac_maxlags), "use_correction": True},
    )
    cov = fit.cov_params()
    block_cov = cov.loc[block_cols, block_cols].to_numpy(dtype=float)
    constraint_cov_rank = int(np.linalg.matrix_rank(block_cov))
    if constraint_cov_rank < len(block_cols):
        return _invalid_row(
            block,
            n=len(base),
            block_columns=len(block_cols),
            design_rank=design_rank,
            design_columns=design_columns,
            constraint_cov_rank=constraint_cov_rank,
            reason="hac_constraint_covariance_rank_deficient",
        ), pd.DataFrame()

    names = list(x_full.columns)
    restriction = np.zeros((len(block_cols), len(names)), dtype=float)
    for i, col in enumerate(block_cols):
        restriction[i, names.index(col)] = 1.0
    wald = fit.wald_test(restriction, scalar=True)

    coef_rows = []
    for col in block_cols:
        beta = float(fit.params[col])
        coef_rows.append(
            {
                "block_id": block.id,
                "coefficient_name": col,
                "coefficient": beta,
                "t_stat": float(fit.tvalues[col]),
                "p_value": float(fit.pvalues[col]),
                "vol_ratio_pct_if_log_dummy": (np.exp(beta) - 1.0) * 100.0,
                "valid_inference": 1,
            }
        )
    coef_df = pd.DataFrame(coef_rows)

    return {
        "block_id": block.id,
        "block_kind": block.kind,
        "n": int(len(base)),
        "block_coefficient_count": int(len(block_cols)),
        "wald_stat": float(np.asarray(wald.statistic).squeeze()),
        "p_value": float(np.asarray(wald.pvalue).squeeze()),
        "delta_r2": float(fit.rsquared - fit_base.rsquared),
        "full_r2": float(fit.rsquared),
        "max_abs_beta": float(coef_df["coefficient"].abs().max()),
        "design_rank": design_rank,
        "design_columns": design_columns,
        "constraint_cov_rank": constraint_cov_rank,
        "constraint_count": int(len(block_cols)),
        "valid_inference": 1,
        "invalid_reason": "",
        "inference": "ols_hac_joint_wald",
    }, coef_df


def _shift_columns(block: BlockSpec, shift: int) -> tuple[str, ...]:
    return tuple(f"control_shift_{shift}__{col}" for col in block.columns)


def _apply_family_fdr(table: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if table.empty:
        return table
    out = table.copy()
    out["p_fdr_bh_family"] = np.nan
    for _, idx in out.groupby(group_cols, dropna=False).groups.items():
        loc = list(idx)
        valid = [
            i for i in loc
            if int(out.at[i, "valid_inference"]) == 1 and np.isfinite(out.at[i, "p_value"])
        ]
        if valid:
            out.loc[valid, "p_fdr_bh_family"] = benjamini_hochberg(out.loc[valid, "p_value"])
    return out


def _run_eras(dataset: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    coef_parts: list[pd.DataFrame] = []
    for era, start, end in ERAS:
        part = _slice_and_purge(dataset, start, end)
        for block in BLOCKS:
            row, coef = _fit_block(part, block)
            if row is not None:
                row.update({"era": era, "test_kind": "registered", "shift_sessions": 0})
                rows.append(row)
                if not coef.empty:
                    coef.insert(0, "era", era)
                    coef.insert(1, "test_kind", "registered")
                    coef.insert(2, "shift_sessions", 0)
                    coef_parts.append(coef)

            for shift in SHIFT_SESSIONS:
                row, coef = _fit_block(part, block, columns=_shift_columns(block, shift))
                if row is None:
                    continue
                row.update({"era": era, "test_kind": "shift_null", "shift_sessions": shift})
                rows.append(row)
                if not coef.empty:
                    coef.insert(0, "era", era)
                    coef.insert(1, "test_kind", "shift_null")
                    coef.insert(2, "shift_sessions", shift)
                    coef_parts.append(coef)

    tests = _apply_family_fdr(pd.DataFrame(rows), ["era", "test_kind"])
    coefs = pd.concat(coef_parts, ignore_index=True) if coef_parts else pd.DataFrame()
    return tests, coefs


def _run_nonoverlap(dataset: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    eligible = dataset.dropna(subset=[TARGET, *BASELINE_CONTINUOUS, *BASELINE_CATEGORICAL]).copy()
    for residue in range(5):
        part = eligible.loc[eligible["session_index"] % 5 == residue].copy().sort_values("date")
        for block in BLOCKS:
            row, _ = _fit_block(
                part,
                block,
                min_level_n=10,
                min_rows=300,
                hac_maxlags=NONOVERLAP_HAC_MAXLAGS,
            )
            if row is None:
                continue
            row.update({"residue": residue, "test_kind": "registered_nonoverlap"})
            rows.append(row)
    return _apply_family_fdr(pd.DataFrame(rows), ["residue", "test_kind"])


def _diagnostics(tests: pd.DataFrame) -> pd.DataFrame:
    if tests.empty:
        return pd.DataFrame()
    rows = []
    for keys, g in tests.groupby(["era", "test_kind"], dropna=False):
        valid = g.loc[g["valid_inference"] == 1]
        rows.append(
            {
                "era": keys[0],
                "test_kind": keys[1],
                "tests_total": int(len(g)),
                "valid_tests": int(len(valid)),
                "invalid_tests": int(len(g) - len(valid)),
                "min_family_fdr": float(valid["p_fdr_bh_family"].min()) if not valid.empty else np.nan,
                "max_delta_r2": float(valid["delta_r2"].max()) if not valid.empty else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["era", "test_kind"]).reset_index(drop=True)


def _gate_table(tests: pd.DataFrame, nonoverlap: pd.DataFrame) -> pd.DataFrame:
    rows = []
    registered = tests.loc[(tests["test_kind"] == "registered") & (tests["valid_inference"] == 1)].copy()
    shifted = tests.loc[(tests["test_kind"] == "shift_null") & (tests["valid_inference"] == 1)].copy()
    no = nonoverlap.loc[nonoverlap["valid_inference"] == 1].copy()

    for block in BLOCKS:
        bid = block.id
        full = registered.loc[(registered["era"] == "history_all") & (registered["block_id"] == bid)]
        full_fdr = float(full["p_fdr_bh_family"].iloc[0]) if len(full) == 1 else np.nan
        full_pass = bool(np.isfinite(full_fdr) and full_fdr <= 0.05)

        later_fdr_passes = 0
        beats_all_shifts_eras = 0
        for era in LATER_ERAS:
            r = registered.loc[(registered["era"] == era) & (registered["block_id"] == bid)]
            if len(r) != 1:
                continue
            rp = float(r["p_value"].iloc[0])
            rfdr = float(r["p_fdr_bh_family"].iloc[0])
            if np.isfinite(rfdr) and rfdr <= 0.10:
                later_fdr_passes += 1
            s = shifted.loc[(shifted["era"] == era) & (shifted["block_id"] == bid)]
            if len(s) == len(SHIFT_SESSIONS) and np.isfinite(rp):
                shift_ps = s["p_value"].astype(float).to_numpy()
                if np.isfinite(shift_ps).all() and rp < float(np.min(shift_ps)):
                    beats_all_shifts_eras += 1

        no_rows = no.loc[no["block_id"] == bid]
        nonoverlap_passes = int((no_rows["p_fdr_bh_family"] <= 0.10).sum())

        gate = (
            full_pass
            and later_fdr_passes >= 2
            and beats_all_shifts_eras >= 2
            and nonoverlap_passes >= 3
        )
        rows.append(
            {
                "block_id": bid,
                "full_history_family_fdr": full_fdr,
                "full_history_pass": int(full_pass),
                "later_eras_family_fdr_lte_0_10": later_fdr_passes,
                "later_eras_registered_p_beats_all_shifts": beats_all_shifts_eras,
                "nonoverlap_residues_family_fdr_lte_0_10": nonoverlap_passes,
                "exploratory_interest_gate_pass": int(gate),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["exploratory_interest_gate_pass", "full_history_family_fdr"],
        ascending=[False, True],
        na_position="last",
    ).reset_index(drop=True)


def run_ganzhi_vol_exploration(
    raw: pd.DataFrame,
    *,
    out_dir: Path,
    manifest: DataManifest | None = None,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    dataset = _build_dataset(raw)
    dataset.to_csv(out_dir / "dataset_ganzhi_vol.csv", index=False)

    tests, coefficients = _run_eras(dataset)
    nonoverlap = _run_nonoverlap(dataset)
    diagnostics = _diagnostics(tests)
    gates = _gate_table(tests, nonoverlap)

    tests.to_csv(out_dir / "era_joint_tests.csv", index=False)
    coefficients.to_csv(out_dir / "block_coefficients.csv", index=False)
    nonoverlap.to_csv(out_dir / "nonoverlap_joint_tests.csv", index=False)
    diagnostics.to_csv(out_dir / "diagnostic_summary.csv", index=False)
    gates.to_csv(out_dir / "exploratory_gate.csv", index=False)
    tests.loc[tests["valid_inference"] == 0].to_csv(out_dir / "invalid_inference_tests.csv", index=False)

    if manifest is not None:
        (out_dir / "data_manifest.json").write_text(manifest.to_json() + "\n", encoding="utf-8")

    metadata = {
        "hypothesis_id": HYPOTHESIS_ID,
        "status": "EXPLORATORY_ONLY_NO_UNSEEN_HISTORY",
        "historical_last_date": "2026-08-14",
        "target": TARGET,
        "raw_target": RAW_TARGET,
        "baseline_continuous": list(BASELINE_CONTINUOUS),
        "baseline_categorical": list(BASELINE_CATEGORICAL),
        "blocks": [{"id": b.id, "kind": b.kind, "columns": list(b.columns)} for b in BLOCKS],
        "shift_null_sessions": list(SHIFT_SESSIONS),
        "hac_maxlags_full_daily": HAC_MAXLAGS,
        "hac_maxlags_nonoverlap": NONOVERLAP_HAC_MAXLAGS,
        "nonoverlap_rule": "original session_index modulo 5",
        "provider_required": "sina",
        "same_day_market_baseline_used": False,
    }
    (out_dir / "run_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# GANZHI_VOL_001 — Direct Ganzhi / Solar-Term Volatility Exploration",
        "",
        "**Evidence status: EXPLORATORY ONLY. Historical outcomes are already exposed.**",
        "",
        "This branch does not use an SSE natal chart. It asks whether direct deterministic Chinese-calendar states add future five-session volatility information beyond lagged volatility, the previous realized move, Gregorian weekday/month effects and a secular time trend.",
        "",
        "The primary target is the natural log of realized volatility computed from exactly t+1..t+5 one-session returns. All market baseline variables are lagged to t-1 or earlier relative to the 09:25 calendar anchor.",
        "",
        "## Era diagnostics",
        "",
    ]
    lines.append(diagnostics.to_markdown(index=False) if not diagnostics.empty else "No eligible era tests.")
    lines.extend(["", "## Frozen exploratory gate", ""])
    lines.append(gates.to_markdown(index=False) if not gates.empty else "No block reached gate evaluation.")
    lines.extend(
        [
            "",
            "A block is only nominated if it passes the full-history family gate, repeats in at least two later eras, beats all three shifted versions in at least two later eras, and survives at least three of five non-overlapping residue-class checks. Historical nomination still does not equal confirmation.",
        ]
    )
    (out_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "dataset": dataset,
        "tests": tests,
        "coefficients": coefficients,
        "nonoverlap": nonoverlap,
        "diagnostics": diagnostics,
        "gates": gates,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run GANZHI_VOL_001 direct calendar-cycle volatility exploration")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--fetch-akshare", action="store_true")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--start", default="19901219")
    parser.add_argument("--end", default="20260814")
    parser.add_argument("--provider", default="sina", choices=("sina",))
    parser.add_argument("--out", type=Path, default=Path("reports/ganzhi_vol_exploratory"))
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

    result = run_ganzhi_vol_exploration(raw, out_dir=args.out, manifest=manifest)
    print(f"rows={len(result['dataset'])}")
    print(f"era_tests={len(result['tests'])}")
    print(f"nonoverlap_tests={len(result['nonoverlap'])}")
    print(f"gate_passes={int(result['gates']['exploratory_interest_gate_pass'].sum()) if not result['gates'].empty else 0}")
    print(f"report={args.out / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
