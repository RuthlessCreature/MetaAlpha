from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

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
