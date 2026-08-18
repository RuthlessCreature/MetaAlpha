from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

from .data_sources import DataManifest, fetch_akshare_index
from .hybrid_model import evaluate_probabilities, make_ridge_logistic_pipeline
from .market_baseline import BASE_CATEGORICAL, BASE_CONTINUOUS, TARGET_DIRECTION, TARGET_RETURN
from .meta_branch import META_CANDIDATE_FEATURES, build_meta_historical_dataset


EXPERIMENT_ID = "META_REGIME_NULL_2025_001"
FIXED_C = 0.01
TEST_START = pd.Timestamp("2025-01-01")
TEST_END = pd.Timestamp("2026-08-17")
SHIFTS = (5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 47, 53, 59, 61, 67, 71, 73,
          79, 83, 89, 97, 101, 109, 113, 127, 131, 137, 149, 157, 167, 181, 197,
          211, 227, 241)
BRANCHES = tuple(META_CANDIDATE_FEATURES)
REGIME_COL = "market_regime_v1"


def _add_market_regime(df: pd.DataFrame) -> pd.DataFrame:
    """Past-only six-state regime: 20d trend sign x prior-252 vol tercile."""
    out = df.copy().sort_values("date").reset_index(drop=True)
    vol = pd.to_numeric(out["vol_lag_20"], errors="raise")
    q_lo = vol.shift(1).rolling(252, min_periods=252).quantile(1.0 / 3.0)
    q_hi = vol.shift(1).rolling(252, min_periods=252).quantile(2.0 / 3.0)
    vol_state = np.where(vol < q_lo, "low", np.where(vol > q_hi, "high", "mid"))
    vol_state = pd.Series(vol_state, index=out.index, dtype="object")
    vol_state.loc[q_lo.isna() | q_hi.isna()] = np.nan
    trend_state = np.where(pd.to_numeric(out["ret_lag_20"], errors="raise") > 0.0, "up", "down")
    out["regime_trend20"] = trend_state
    out["regime_vol20_tercile"] = vol_state
    out[REGIME_COL] = out["regime_trend20"].astype(str) + "|" + out["regime_vol20_tercile"].astype(str)
    out.loc[out["regime_vol20_tercile"].isna(), REGIME_COL] = np.nan
    return out


def _interaction_columns(frame: pd.DataFrame, symbolic_cols: list[str], *, prefix: str) -> list[str]:
    names: list[str] = []
    for col in symbolic_cols:
        name = f"{prefix}__{col}"
        frame[name] = frame[REGIME_COL].astype(str) + "||" + frame[col].astype(str)
        names.append(name)
    return names


def _fit_prob(train: pd.DataFrame, test: pd.DataFrame, categorical: list[str]) -> np.ndarray:
    model = make_ridge_logistic_pipeline(list(BASE_CONTINUOUS), categorical, C=FIXED_C)
    y = train[TARGET_DIRECTION].astype(int).to_numpy()
    model.fit(train[list(BASE_CONTINUOUS) + categorical], y)
    return model.predict_proba(test[list(BASE_CONTINUOUS) + categorical])[:, 1].astype(float)


def _metrics(y: np.ndarray, p: np.ndarray, returns: np.ndarray) -> dict[str, float]:
    m = evaluate_probabilities(y, p, returns)
    return {
        "log_loss": float(m.log_loss),
        "brier_score": float(m.brier_score),
        "roc_auc": float(m.roc_auc),
        "accuracy": float(m.accuracy),
        "calibration_slope": float(m.calibration_slope),
        "probability_spread_return": float(m.probability_spread_return),
    }


def _prepare_common(raw: pd.DataFrame) -> pd.DataFrame:
    dataset = build_meta_historical_dataset(raw)
    dataset = _add_market_regime(dataset)
    # All shifted-state competitors must use exactly the same rows.
    dataset = dataset.iloc[max(SHIFTS):].copy().reset_index(drop=True)
    required = [REGIME_COL, TARGET_DIRECTION, TARGET_RETURN, *BASE_CONTINUOUS, *BASE_CATEGORICAL]
    for cols in META_CANDIDATE_FEATURES.values():
        required.extend(cols)
    dataset = dataset.dropna(subset=list(dict.fromkeys(required))).copy().reset_index(drop=True)
    return dataset


def run(raw: pd.DataFrame, *, manifest: DataManifest | None = None, out_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    full = _add_market_regime(build_meta_historical_dataset(raw))

    # Build every shifted state before the common max-shift cut.
    shifted_cols: dict[tuple[str, int], list[str]] = {}
    for branch, cols in META_CANDIDATE_FEATURES.items():
        for shift in SHIFTS:
            names: list[str] = []
            for col in cols:
                name = f"nullshift_{branch}_{shift}__{col}"
                full[name] = full[col].shift(shift)
                names.append(name)
            shifted_cols[(branch, shift)] = names

    common = full.iloc[max(SHIFTS):].copy().reset_index(drop=True)
    required = [REGIME_COL, TARGET_DIRECTION, TARGET_RETURN, *BASE_CONTINUOUS, *BASE_CATEGORICAL]
    for cols in META_CANDIDATE_FEATURES.values():
        required.extend(cols)
    for names in shifted_cols.values():
        required.extend(names)
    common = common.dropna(subset=list(dict.fromkeys(required))).copy().reset_index(drop=True)

    train = common.loc[common["date"] < TEST_START].copy().reset_index(drop=True)
    test = common.loc[(common["date"] >= TEST_START) & (common["date"] <= TEST_END)].copy().reset_index(drop=True)
    if len(train) < 7000:
        raise ValueError(f"insufficient common training rows: {len(train)}")
    if len(test) < 300:
        raise ValueError(f"insufficient common test rows: {len(test)}")

    y = test[TARGET_DIRECTION].astype(int).to_numpy()
    returns = test[TARGET_RETURN].astype(float).to_numpy()

    r0_cat = list(BASE_CATEGORICAL)
    r1_cat = list(BASE_CATEGORICAL) + [REGIME_COL]
    p_r0 = _fit_prob(train, test, r0_cat)
    p_r1 = _fit_prob(train, test, r1_cat)
    r0m = _metrics(y, p_r0, returns)
    r1m = _metrics(y, p_r1, returns)

    predictions = pd.DataFrame({
        "date": test["date"].to_numpy(),
        "target": y,
        "same_session_return": returns,
        REGIME_COL: test[REGIME_COL].to_numpy(),
        "R0_prob": p_r0,
        "R1_prob": p_r1,
    })

    actual_rows: list[dict[str, object]] = []
    null_rows: list[dict[str, object]] = []
    regime_rows: list[dict[str, object]] = []

    for branch in BRANCHES:
        sym = list(META_CANDIDATE_FEATURES[branch])

        actual_train = train.copy()
        actual_test = test.copy()
        interaction_actual = _interaction_columns(actual_train, sym, prefix=f"r3_{branch}")
        _interaction_columns(actual_test, sym, prefix=f"r3_{branch}")

        r2_cat = r1_cat + sym
        r3_cat = r2_cat + interaction_actual
        p_r2 = _fit_prob(actual_train, actual_test, r2_cat)
        p_r3 = _fit_prob(actual_train, actual_test, r3_cat)
        m2 = _metrics(y, p_r2, returns)
        m3 = _metrics(y, p_r3, returns)
        predictions[f"{branch}_R2_prob"] = p_r2
        predictions[f"{branch}_R3_prob"] = p_r3

        actual_ll_imp = r1m["log_loss"] - m3["log_loss"]
        actual_br_imp = r1m["brier_score"] - m3["brier_score"]

        branch_null: list[dict[str, object]] = []
        for shift in SHIFTS:
            null_sym = shifted_cols[(branch, shift)]
            null_train = train.copy()
            null_test = test.copy()
            interaction_null = _interaction_columns(null_train, null_sym, prefix=f"n3_{branch}_{shift}")
            _interaction_columns(null_test, null_sym, prefix=f"n3_{branch}_{shift}")
            n3_cat = r1_cat + null_sym + interaction_null
            p_n3 = _fit_prob(null_train, null_test, n3_cat)
            mn = _metrics(y, p_n3, returns)
            row = {
                "branch": branch,
                "shift_sessions": shift,
                **mn,
                "logloss_improvement_vs_R1": r1m["log_loss"] - mn["log_loss"],
                "brier_improvement_vs_R1": r1m["brier_score"] - mn["brier_score"],
            }
            null_rows.append(row)
            branch_null.append(row)

        null_ll = np.array([float(r["logloss_improvement_vs_R1"]) for r in branch_null])
        null_br = np.array([float(r["brier_improvement_vs_R1"]) for r in branch_null])
        ll_percentile = float(np.mean(null_ll <= actual_ll_imp))
        br_percentile = float(np.mean(null_br <= actual_br_imp))
        ll_p = float((1 + np.sum(null_ll >= actual_ll_imp)) / (len(null_ll) + 1))
        br_p = float((1 + np.sum(null_br >= actual_br_imp)) / (len(null_br) + 1))

        actual_rows.append({
            "branch": branch,
            "R2_log_loss": m2["log_loss"],
            "R2_brier_score": m2["brier_score"],
            "R2_logloss_improvement_vs_R1": r1m["log_loss"] - m2["log_loss"],
            "R2_brier_improvement_vs_R1": r1m["brier_score"] - m2["brier_score"],
            "R3_log_loss": m3["log_loss"],
            "R3_brier_score": m3["brier_score"],
            "R3_roc_auc": m3["roc_auc"],
            "R3_accuracy": m3["accuracy"],
            "R3_logloss_improvement_vs_R1": actual_ll_imp,
            "R3_brier_improvement_vs_R1": actual_br_imp,
            "R3_minus_R2_logloss_improvement": m2["log_loss"] - m3["log_loss"],
            "R3_minus_R2_brier_improvement": m2["brier_score"] - m3["brier_score"],
            "null_R3_logloss_mean_improvement": float(null_ll.mean()),
            "null_R3_logloss_p95_improvement": float(np.quantile(null_ll, 0.95)),
            "R3_logloss_percentile_vs_shift_null": ll_percentile,
            "R3_logloss_empirical_p_one_sided": ll_p,
            "null_R3_brier_mean_improvement": float(null_br.mean()),
            "null_R3_brier_p95_improvement": float(np.quantile(null_br, 0.95)),
            "R3_brier_percentile_vs_shift_null": br_percentile,
            "R3_brier_empirical_p_one_sided": br_p,
        })

        for regime, idx in predictions.groupby(REGIME_COL).groups.items():
            idx_arr = np.asarray(list(idx), dtype=int)
            if len(idx_arr) < 10:
                continue
            yr = y[idx_arr]
            rr = returns[idx_arr]
            r1_reg = _metrics(yr, p_r1[idx_arr], rr)
            r3_reg = _metrics(yr, p_r3[idx_arr], rr)
            regime_rows.append({
                "branch": branch,
                REGIME_COL: regime,
                "n": len(idx_arr),
                "R1_log_loss": r1_reg["log_loss"],
                "R3_log_loss": r3_reg["log_loss"],
                "R3_logloss_improvement_vs_R1": r1_reg["log_loss"] - r3_reg["log_loss"],
                "R1_brier_score": r1_reg["brier_score"],
                "R3_brier_score": r3_reg["brier_score"],
                "R3_brier_improvement_vs_R1": r1_reg["brier_score"] - r3_reg["brier_score"],
            })

    actual = pd.DataFrame(actual_rows).sort_values("R3_logloss_improvement_vs_R1", ascending=False).reset_index(drop=True)
    nulls = pd.DataFrame(null_rows)
    regime = pd.DataFrame(regime_rows)
    baseline = pd.DataFrame([
        {"model_id": "R0_baseline", **r0m},
        {"model_id": "R1_market_regime", **r1m},
    ])

    outputs = {
        "baseline_ladder": baseline,
        "actual_vs_null": actual,
        "shift_nulls": nulls,
        "regime_specific": regime,
        "predictions": predictions,
    }

    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, frame in outputs.items():
            frame.to_csv(out_dir / f"{name}.csv", index=False)
        metadata = {
            "experiment_id": EXPERIMENT_ID,
            "status": "RETROSPECTIVE_DESCRIPTIVE",
            "fixed_C": FIXED_C,
            "train_rows": len(train),
            "test_rows": len(test),
            "train_first": train["date"].iloc[0].strftime("%Y-%m-%d"),
            "train_last": train["date"].iloc[-1].strftime("%Y-%m-%d"),
            "test_first": test["date"].iloc[0].strftime("%Y-%m-%d"),
            "test_last": test["date"].iloc[-1].strftime("%Y-%m-%d"),
            "regime": "ret_lag_20 sign x past-only prior-252 vol_lag_20 tercile",
            "shifts": list(SHIFTS),
            "branches": list(BRANCHES),
        }
        (out_dir / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if manifest is not None:
            (out_dir / "data_manifest.json").write_text(manifest.to_json() + "\n", encoding="utf-8")

        show = actual[[
            "branch", "R2_logloss_improvement_vs_R1", "R3_logloss_improvement_vs_R1",
            "R3_minus_R2_logloss_improvement", "R3_brier_improvement_vs_R1",
            "R3_logloss_percentile_vs_shift_null", "R3_logloss_empirical_p_one_sided",
        ]]
        lines = [
            f"# {EXPERIMENT_ID} — Regime-conditioned symbolic matched-null diagnostic",
            "",
            "**RETROSPECTIVE / DESCRIPTIVE ONLY. Does not modify META_FWD_001.**",
            "",
            f"Common train rows: **{len(train):,}**; test rows: **{len(test):,}** ({test['date'].min().date()} .. {test['date'].max().date()}).",
            f"Fixed C: **{FIXED_C}**. Regime: 20-session trend sign × past-only 252-session volatility tercile.",
            "",
            "## Ordinary model ladder",
            "",
            tabulate(baseline, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
            "",
            "## Traditional R2/R3 versus shifted-state R3 null family",
            "",
            tabulate(show, headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
            "",
            "Interpretation: R2 tests symbolic main effects after market regime; R3 additionally tests regime×symbolic interactions. A positive R3-R2 improvement suggests conditional rather than universal value. Scientific uniqueness additionally requires the actual R3 to sit near the extreme top of its identical-capacity shifted-state null family.",
            "",
            "## Regime-specific R3 improvement",
            "",
            tabulate(regime.sort_values(["branch", "R3_logloss_improvement_vs_R1"], ascending=[True, False]), headers="keys", tablefmt="github", showindex=False, floatfmt=".6g"),
            "",
        ]
        if manifest is not None:
            lines.extend(["## Data manifest", "", "```json", manifest.to_json(), "```", ""])
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
