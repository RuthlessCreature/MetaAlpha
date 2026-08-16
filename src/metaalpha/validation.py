from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class WalkForwardSplit:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


def benjamini_hochberg(p_values: Iterable[float]) -> np.ndarray:
    """Benjamini-Hochberg FDR-adjusted p-values preserving input order."""
    p = np.asarray(list(p_values), dtype=float)
    out = np.full_like(p, np.nan)
    valid = np.isfinite(p)
    pv = p[valid]
    if pv.size == 0:
        return out

    order = np.argsort(pv)
    ranked = pv[order]
    m = ranked.size
    adjusted = ranked * m / np.arange(1, m + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    restored = np.empty_like(adjusted)
    restored[order] = adjusted
    out[valid] = restored
    return out


def expanding_walk_forward_splits(
    n_rows: int,
    *,
    min_train: int,
    test_size: int,
    step: int | None = None,
) -> list[WalkForwardSplit]:
    if min_train <= 0 or test_size <= 0:
        raise ValueError("min_train and test_size must be positive")
    step = test_size if step is None else step
    if step <= 0:
        raise ValueError("step must be positive")

    splits: list[WalkForwardSplit] = []
    test_start = min_train
    while test_start + test_size <= n_rows:
        splits.append(WalkForwardSplit(0, test_start, test_start, test_start + test_size))
        test_start += step
    return splits


def evaluate_categorical_feature(
    df: pd.DataFrame,
    feature: str,
    target: str,
    *,
    min_n: int = 30,
) -> pd.DataFrame:
    """One-vs-rest univariate screening for a categorical feature."""
    rows: list[dict] = []
    base = df[[feature, target]].dropna()
    overall = base[target].to_numpy(dtype=float)
    for level, g in base.groupby(feature, dropna=False):
        x = g[target].to_numpy(dtype=float)
        rest = base.loc[base[feature] != level, target].to_numpy(dtype=float)
        if x.size < min_n or rest.size < min_n:
            continue
        test = stats.ttest_ind(x, rest, equal_var=False, nan_policy="omit")
        pooled_scale = np.nanstd(overall, ddof=1)
        effect = (np.nanmean(x) - np.nanmean(rest)) / pooled_scale if pooled_scale > 0 else np.nan
        rows.append(
            {
                "feature": feature,
                "level": level,
                "n": int(x.size),
                "mean_target": float(np.nanmean(x)),
                "rest_mean": float(np.nanmean(rest)),
                "effect_std": float(effect) if math.isfinite(effect) else np.nan,
                "t_stat": float(test.statistic),
                "p_value": float(test.pvalue),
            }
        )
    result = pd.DataFrame(rows)
    if not result.empty:
        result["p_fdr_bh"] = benjamini_hochberg(result["p_value"])
        result = result.sort_values(["p_fdr_bh", "p_value"]).reset_index(drop=True)
    return result


def evaluate_categorical_family(
    df: pd.DataFrame,
    features: Sequence[str],
    target: str,
    *,
    family_name: str,
    min_n: int = 30,
) -> pd.DataFrame:
    """Evaluate a preregistered feature family with one FDR correction across all tests.

    Applying BH separately to each feature understates the multiplicity of a
    multi-feature hypothesis. This function deliberately recomputes FDR across
    every tested level in the registered family.
    """
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"missing registered features for {family_name}: {missing}")

    parts: list[pd.DataFrame] = []
    for feature in features:
        r = evaluate_categorical_feature(df, feature, target, min_n=min_n)
        if not r.empty:
            r = r.drop(columns=["p_fdr_bh"], errors="ignore")
            parts.append(r)

    if not parts:
        return pd.DataFrame()

    out = pd.concat(parts, ignore_index=True)
    out["family"] = family_name
    out["p_fdr_bh_family"] = benjamini_hochberg(out["p_value"])
    return out.sort_values(["p_fdr_bh_family", "p_value"]).reset_index(drop=True)


def walk_forward_categorical_stability(
    df: pd.DataFrame,
    *,
    feature: str,
    target: str,
    min_train: int = 1000,
    test_size: int = 250,
    min_n: int = 15,
) -> pd.DataFrame:
    """Measure a frozen categorical feature on successive future-only test blocks.

    This is a stability diagnostic, not a model-tuning loop. The rule and level
    definitions are frozen before the folds are inspected. No test observation
    is used to construct an earlier fold.
    """
    if feature not in df.columns or target not in df.columns:
        raise ValueError("feature and target must exist in dataframe")

    ordered = df.sort_values("date").reset_index(drop=True) if "date" in df.columns else df.reset_index(drop=True)
    if len(ordered) < min_train + test_size:
        return pd.DataFrame()

    rows: list[pd.DataFrame] = []
    for fold, split in enumerate(
        expanding_walk_forward_splits(len(ordered), min_train=min_train, test_size=test_size),
        start=1,
    ):
        test = ordered.iloc[split.test_start:split.test_end]
        r = evaluate_categorical_feature(test, feature, target, min_n=min_n)
        if r.empty:
            continue
        r = r.drop(columns=["p_fdr_bh"], errors="ignore")
        r.insert(0, "fold", fold)
        r["test_start_row"] = split.test_start
        r["test_end_row"] = split.test_end
        if "date" in test.columns:
            r["test_first_date"] = pd.to_datetime(test["date"]).min().strftime("%Y-%m-%d")
            r["test_last_date"] = pd.to_datetime(test["date"]).max().strftime("%Y-%m-%d")
        rows.append(r)

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)
