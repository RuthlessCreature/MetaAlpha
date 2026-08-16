from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .data_sources import DataManifest, fetch_akshare_index
from .qimen_market import add_qimen_market_features
from .validation import benjamini_hochberg


HYPOTHESIS_ID = "QIMEN_MARKET_001"
TARGET = "ret_session_t"
HAC_MAXLAGS = 5
MIN_LEVEL_N = 50
MIN_ROWS = 500
SHIFT_SESSIONS = (17, 31, 47)

BASELINE_CONTINUOUS = (
    "ret_session_lag1",
    "vol_back_5_lag1",
    "vol_back_20_lag1",
    "normalized_time",
    "normalized_time_squared",
)
BASELINE_CATEGORICAL = ("calendar_weekday", "calendar_month")

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
    column: str
    family: str = "qimen"


QIMEN_BLOCKS = (
    BlockSpec("ju_state", "qimen__v1__dun_ju_yuan"),
    BlockSpec("duty_star_door", "qimen__v1__duty_star_door"),
    BlockSpec("duty_landings", "qimen__v1__duty_landings"),
    BlockSpec("rotation_state", "qimen__v1__rotation_state"),
    BlockSpec("xun_target_state", "qimen__v1__xun_target_state"),
    BlockSpec("void_relation_state", "qimen__v1__void_relation_state"),
    BlockSpec("yima_relation_state", "qimen__v1__yima_relation_state"),
    BlockSpec("duty_door_palace_composition", "qimen__v1__duty_door_palace_composition"),
    BlockSpec("yima_palace_composition", "qimen__v1__yima_palace_composition"),
)
BENCHMARK_BLOCKS = (
    BlockSpec("direct_solar_term", "qimen__v1__solar_term", "ingredient_benchmark"),
    BlockSpec("direct_day_pillar", "qimen__v1__day_pillar", "ingredient_benchmark"),
    BlockSpec("direct_hour_pillar", "qimen__v1__hour_pillar", "ingredient_benchmark"),
)


def _build_dataset(raw: pd.DataFrame) -> pd.DataFrame:
    if not {"date", "close"}.issubset(raw.columns):
        raise ValueError("raw data requires date and close")
    out = raw.copy().sort_values("date").reset_index(drop=True)
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.normalize()
    if "symbol" not in out.columns:
        out["symbol"] = "INDEX_000001"
    out["session_index"] = np.arange(len(out), dtype=int)

    out[TARGET] = out["close"].astype(float).pct_change()
    lagged_return = out[TARGET].shift(1)
    out["ret_session_lag1"] = lagged_return
    out["vol_back_5_lag1"] = lagged_return.rolling(5, min_periods=5).std()
    out["vol_back_20_lag1"] = lagged_return.rolling(20, min_periods=20).std()
    denom = max(len(out) - 1, 1)
    out["normalized_time"] = out["session_index"] / float(denom)
    out["normalized_time_squared"] = out["normalized_time"] ** 2
    out["calendar_weekday"] = out["date"].dt.weekday.astype(str)
    out["calendar_month"] = out["date"].dt.month.astype(str)

    out = add_qimen_market_features(out)

    for block in QIMEN_BLOCKS:
        for shift in SHIFT_SESSIONS:
            out[f"control_shift_{shift}__{block.column}"] = out[block.column].shift(shift)
    return out


def _slice_dates(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    dates = pd.to_datetime(df["date"], errors="raise")
    mask = pd.Series(True, index=df.index)
    if start is not None:
        mask &= dates >= pd.Timestamp(start)
    if end is not None:
        mask &= dates <= pd.Timestamp(end)
    return df.loc[mask].copy().sort_values("date").reset_index(drop=True)


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


def _invalid_row(block: BlockSpec, *, n: int, k: int, rank: int, cols: int, cov_rank: int, reason: str) -> dict[str, object]:
    return {
        "block_id": block.id,
        "family": block.family,
        "n": int(n),
        "block_coefficient_count": int(k),
        "wald_stat": np.nan,
        "p_value": np.nan,
        "delta_r2": np.nan,
        "full_r2": np.nan,
        "max_abs_beta_bps": np.nan,
        "design_rank": int(rank),
        "design_columns": int(cols),
        "constraint_cov_rank": int(cov_rank),
        "constraint_count": int(k),
        "valid_inference": 0,
        "invalid_reason": reason,
    }


def _fit_block(
    df: pd.DataFrame,
    block: BlockSpec,
    *,
    column: str | None = None,
    min_level_n: int = MIN_LEVEL_N,
    min_rows: int = MIN_ROWS,
) -> tuple[dict[str, object] | None, pd.DataFrame]:
    column = block.column if column is None else column
    needed = ["date", TARGET, *BASELINE_CONTINUOUS, *BASELINE_CATEGORICAL, column]
    base = df[needed].dropna().copy().sort_values("date").reset_index(drop=True)
    if len(base) < min_rows:
        return None, pd.DataFrame()

    values = _collapse_rare(base[column], min_level_n)
    if values.nunique() < 2:
        return None, pd.DataFrame()
    raw_dummies = pd.get_dummies(values, prefix="level", drop_first=True, dtype=float).reset_index(drop=True)
    if raw_dummies.shape[1] == 0:
        return None, pd.DataFrame()

    level_labels = [str(c).removeprefix("level_") for c in raw_dummies.columns]
    raw_dummies.columns = [f"tested__{block.id}__{i}" for i in range(raw_dummies.shape[1])]
    tested_cols = list(raw_dummies.columns)
    x_base_raw = _baseline_design(base)
    x_base = sm.add_constant(x_base_raw, prepend=True, has_constant="add")
    x_full = sm.add_constant(pd.concat([x_base_raw, raw_dummies], axis=1), prepend=True, has_constant="add")
    y = base[TARGET].to_numpy(dtype=float)

    design = x_full.to_numpy(dtype=float)
    rank = int(np.linalg.matrix_rank(design))
    ncols = int(x_full.shape[1])
    if rank < ncols:
        return _invalid_row(block, n=len(base), k=len(tested_cols), rank=rank, cols=ncols, cov_rank=0, reason="design_matrix_rank_deficient"), pd.DataFrame()

    fit_base = sm.OLS(y, x_base).fit()
    fit = sm.OLS(y, x_full).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_MAXLAGS, "use_correction": True})
    cov = fit.cov_params().loc[tested_cols, tested_cols].to_numpy(dtype=float)
    cov_rank = int(np.linalg.matrix_rank(cov))
    if cov_rank < len(tested_cols):
        return _invalid_row(block, n=len(base), k=len(tested_cols), rank=rank, cols=ncols, cov_rank=cov_rank, reason="hac_constraint_covariance_rank_deficient"), pd.DataFrame()

    names = list(x_full.columns)
    restriction = np.zeros((len(tested_cols), len(names)), dtype=float)
    for i, col in enumerate(tested_cols):
        restriction[i, names.index(col)] = 1.0
    wald = fit.wald_test(restriction, scalar=True)

    coef_rows = []
    for col, level in zip(tested_cols, level_labels):
        beta = float(fit.params[col])
        coef_rows.append({
            "block_id": block.id,
            "family": block.family,
            "level": level,
            "coefficient": beta,
            "coefficient_bps": beta * 10000.0,
            "t_stat": float(fit.tvalues[col]),
            "p_value": float(fit.pvalues[col]),
            "valid_inference": 1,
        })
    coef_df = pd.DataFrame(coef_rows)

    return {
        "block_id": block.id,
        "family": block.family,
        "n": int(len(base)),
        "block_coefficient_count": int(len(tested_cols)),
        "wald_stat": float(np.asarray(wald.statistic).squeeze()),
        "p_value": float(np.asarray(wald.pvalue).squeeze()),
        "delta_r2": float(fit.rsquared - fit_base.rsquared),
        "full_r2": float(fit.rsquared),
        "max_abs_beta_bps": float(coef_df["coefficient_bps"].abs().max()),
        "design_rank": rank,
        "design_columns": ncols,
        "constraint_cov_rank": cov_rank,
        "constraint_count": int(len(tested_cols)),
        "valid_inference": 1,
        "invalid_reason": "",
    }, coef_df


def _apply_fdr(table: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if table.empty:
        return table
    out = table.copy()
    out["p_fdr_bh_family"] = np.nan
    for _, idx in out.groupby(group_cols, dropna=False).groups.items():
        loc = list(idx)
        valid = [i for i in loc if int(out.at[i, "valid_inference"]) == 1 and np.isfinite(out.at[i, "p_value"])]
        if valid:
            out.loc[valid, "p_fdr_bh_family"] = benjamini_hochberg(out.loc[valid, "p_value"])
    return out


def _run_eras(dataset: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    coefs: list[pd.DataFrame] = []
    bench_rows: list[dict[str, object]] = []

    for era, start, end in ERAS:
        part = _slice_dates(dataset, start, end)
        for block in QIMEN_BLOCKS:
            row, coef = _fit_block(part, block)
            if row is not None:
                row.update({"era": era, "test_kind": "registered", "shift_sessions": 0})
                rows.append(row)
                if not coef.empty:
                    coef.insert(0, "era", era); coef.insert(1, "test_kind", "registered"); coef.insert(2, "shift_sessions", 0)
                    coefs.append(coef)
            for shift in SHIFT_SESSIONS:
                shifted_col = f"control_shift_{shift}__{block.column}"
                row, coef = _fit_block(part, block, column=shifted_col)
                if row is None:
                    continue
                row.update({"era": era, "test_kind": "shift_null", "shift_sessions": shift})
                rows.append(row)
                if not coef.empty:
                    coef.insert(0, "era", era); coef.insert(1, "test_kind", "shift_null"); coef.insert(2, "shift_sessions", shift)
                    coefs.append(coef)

        for block in BENCHMARK_BLOCKS:
            row, _ = _fit_block(part, block)
            if row is not None:
                row.update({"era": era, "test_kind": "ingredient_benchmark", "shift_sessions": 0})
                bench_rows.append(row)

    tests = _apply_fdr(pd.DataFrame(rows), ["era", "test_kind"])
    benchmarks = _apply_fdr(pd.DataFrame(bench_rows), ["era", "test_kind"])
    coef_df = pd.concat(coefs, ignore_index=True) if coefs else pd.DataFrame()
    return tests, benchmarks, coef_df


def _gate_table(tests: pd.DataFrame) -> pd.DataFrame:
    registered = tests.loc[(tests["test_kind"] == "registered") & (tests["valid_inference"] == 1)]
    shifted = tests.loc[(tests["test_kind"] == "shift_null") & (tests["valid_inference"] == 1)]
    rows = []
    for block in QIMEN_BLOCKS:
        full = registered.loc[(registered["era"] == "history_all") & (registered["block_id"] == block.id)]
        full_fdr = float(full["p_fdr_bh_family"].iloc[0]) if len(full) == 1 else np.nan
        later_pass = 0
        beats_shifts = 0
        invalid = int(((tests["block_id"] == block.id) & (tests["test_kind"] == "registered") & (tests["valid_inference"] == 0)).sum())
        for era in LATER_ERAS:
            r = registered.loc[(registered["era"] == era) & (registered["block_id"] == block.id)]
            if len(r) != 1:
                continue
            rp = float(r["p_value"].iloc[0]); rfdr = float(r["p_fdr_bh_family"].iloc[0])
            if np.isfinite(rfdr) and rfdr <= 0.10:
                later_pass += 1
            s = shifted.loc[(shifted["era"] == era) & (shifted["block_id"] == block.id)]
            if len(s) == 3 and np.isfinite(rp) and np.isfinite(s["p_value"].astype(float)).all():
                if rp < float(s["p_value"].astype(float).min()):
                    beats_shifts += 1
        gate = bool(np.isfinite(full_fdr) and full_fdr <= 0.05 and later_pass >= 2 and beats_shifts >= 2 and invalid == 0)
        rows.append({
            "block_id": block.id,
            "full_history_family_fdr": full_fdr,
            "later_eras_family_fdr_lte_0_10": later_pass,
            "later_eras_registered_p_beats_all_shifts": beats_shifts,
            "invalid_registered_tests": invalid,
            "exploratory_interest_gate_pass": int(gate),
        })
    return pd.DataFrame(rows).sort_values(["exploratory_interest_gate_pass", "full_history_family_fdr"], ascending=[False, True], na_position="last").reset_index(drop=True)


def _diagnostics(tests: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, g in tests.groupby(["era", "test_kind"], dropna=False):
        valid = g.loc[g["valid_inference"] == 1]
        rows.append({
            "era": keys[0], "test_kind": keys[1], "tests_total": int(len(g)),
            "valid_tests": int(len(valid)), "invalid_tests": int(len(g)-len(valid)),
            "min_family_fdr": float(valid["p_fdr_bh_family"].min()) if not valid.empty else np.nan,
            "max_delta_r2": float(valid["delta_r2"].max()) if not valid.empty else np.nan,
        })
    return pd.DataFrame(rows).sort_values(["era", "test_kind"]).reset_index(drop=True)


def run_qimen_market_exploration(raw: pd.DataFrame, *, out_dir: Path, manifest: DataManifest | None = None) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    dataset = _build_dataset(raw)
    dataset.to_csv(out_dir / "dataset_qimen_market.csv", index=False)
    tests, benchmarks, coefficients = _run_eras(dataset)
    gates = _gate_table(tests)
    diagnostics = _diagnostics(tests)

    tests.to_csv(out_dir / "qimen_joint_tests.csv", index=False)
    benchmarks.to_csv(out_dir / "ingredient_benchmarks.csv", index=False)
    coefficients.to_csv(out_dir / "qimen_coefficients.csv", index=False)
    gates.to_csv(out_dir / "exploratory_gate.csv", index=False)
    diagnostics.to_csv(out_dir / "diagnostic_summary.csv", index=False)
    tests.loc[tests["valid_inference"] == 0].to_csv(out_dir / "invalid_inference_tests.csv", index=False)
    if manifest is not None:
        (out_dir / "data_manifest.json").write_text(manifest.to_json() + "\n", encoding="utf-8")

    meta = {
        "hypothesis_id": HYPOTHESIS_ID,
        "status": "EXPLORATORY_ONLY_NO_UNSEEN_HISTORY",
        "engine": "QIMEN_V1",
        "market_anchor": "09:25 Asia/Shanghai",
        "target": TARGET,
        "same_session_market_predictor_used": False,
        "baseline_continuous": list(BASELINE_CONTINUOUS),
        "baseline_categorical": list(BASELINE_CATEGORICAL),
        "qimen_blocks": [b.id for b in QIMEN_BLOCKS],
        "ingredient_benchmarks": [b.id for b in BENCHMARK_BLOCKS],
        "shift_null_sessions": list(SHIFT_SESSIONS),
        "hac_maxlags": HAC_MAXLAGS,
        "provider_required": "sina",
        "aggregate_score_defined": False,
    }
    (out_dir / "run_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# QIMEN_MARKET_001 — Historical Exploration",
        "",
        "**Evidence status: EXPLORATORY ONLY. Historical outcomes are already exposed.**",
        "",
        "The QIMEN_V1 plate is fixed at 09:25 Asia/Shanghai. The target is the same session's close-to-close return. All market baseline variables are known by t-1 close.",
        "",
        "No auspiciousness, fortune or market-direction score is used. Registered blocks are raw plate states.",
        "",
        "## Era diagnostics", "",
        diagnostics.to_markdown(index=False) if not diagnostics.empty else "No eligible tests.",
        "", "## Frozen exploratory gate", "",
        gates.to_markdown(index=False) if not gates.empty else "No gate rows.",
        "",
        "A block is nominated only if it passes full-history family correction, repeats in at least two later eras, beats all three shifted controls in at least two later eras, and has no invalid registered inference. Historical nomination would still require a separate future-only experiment.",
    ]
    (out_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"dataset": dataset, "tests": tests, "benchmarks": benchmarks, "coefficients": coefficients, "gates": gates, "diagnostics": diagnostics}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run QIMEN_MARKET_001 historical exploration")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--fetch-akshare", action="store_true")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--start", default="19901219")
    parser.add_argument("--end", default="20260814")
    parser.add_argument("--provider", default="sina", choices=("sina",))
    parser.add_argument("--out", type=Path, default=Path("reports/qimen_market_exploratory"))
    args = parser.parse_args()

    manifest: DataManifest | None = None
    if args.fetch_akshare:
        raw, manifest = fetch_akshare_index(symbol=args.symbol, start_date=args.start, end_date=args.end, provider=args.provider)
    else:
        raw = pd.read_csv(args.input)
    result = run_qimen_market_exploration(raw, out_dir=args.out, manifest=manifest)
    print(f"rows={len(result['dataset'])}")
    print(f"tests={len(result['tests'])}")
    print(f"gate_passes={int(result['gates']['exploratory_interest_gate_pass'].sum()) if not result['gates'].empty else 0}")
    print(f"report={args.out / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
