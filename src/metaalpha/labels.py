from __future__ import annotations

import re

import numpy as np
import pandas as pd


def add_forward_labels(
    df: pd.DataFrame,
    *,
    close_col: str = "close",
    group_col: str | None = "symbol",
    horizons: tuple[int, ...] = (1, 5, 20),
    extreme_loss_threshold: float = -0.03,
) -> pd.DataFrame:
    """Create strictly future-only labels from close prices.

    For a row at session ``t``:

    - ``ret_fwd_h`` uses ``C[t+h] / C[t] - 1``;
    - ``vol_fwd_h`` uses exactly the one-session returns at ``t+1..t+h``.

    The implementation sorts defensively within symbol before shifting. No
    present/past return is permitted inside a forward-volatility target.
    """
    out = df.copy()
    sort_cols = [c for c in (group_col, "date") if c and c in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols).reset_index(drop=True)

    if group_col and group_col in out.columns:
        grouped = out.groupby(group_col, sort=False)[close_col]
        for h in horizons:
            out[f"ret_fwd_{h}"] = grouped.shift(-h) / out[close_col] - 1.0
        out["ret_1"] = grouped.pct_change()
    else:
        for h in horizons:
            out[f"ret_fwd_{h}"] = out[close_col].shift(-h) / out[close_col] - 1.0
        out["ret_1"] = out[close_col].pct_change()

    if 1 in horizons:
        out["dir_fwd_1"] = np.where(
            out["ret_fwd_1"].notna(), (out["ret_fwd_1"] > 0).astype("int8"), np.nan
        )
        out["extreme_loss_fwd_1"] = np.where(
            out["ret_fwd_1"].notna(),
            (out["ret_fwd_1"] <= extreme_loss_threshold).astype("int8"),
            np.nan,
        )

    # At t, rolling(h) evaluated at t+h contains ret_1[t+1..t+h].
    # Shifting that result backward by h places the strictly future window on t.
    for h in (5, 20):
        if group_col and group_col in out.columns:
            out[f"vol_fwd_{h}"] = out.groupby(group_col, sort=False)["ret_1"].transform(
                lambda s: s.rolling(h, min_periods=h).std().shift(-h)
            )
        else:
            out[f"vol_fwd_{h}"] = out["ret_1"].rolling(h, min_periods=h).std().shift(-h)

    return out


def target_forward_horizon(target: str) -> int:
    """Return how many future sessions a registered target consumes."""
    if target in {"dir_fwd_1", "extreme_loss_fwd_1"}:
        return 1
    match = re.fullmatch(r"(?:ret|vol)_fwd_(\d+)", target)
    if not match:
        raise ValueError(f"unknown forward target horizon: {target}")
    horizon = int(match.group(1))
    if horizon <= 0:
        raise ValueError("forward horizon must be positive")
    return horizon


def purge_forward_boundary(
    df: pd.DataFrame,
    *,
    target: str,
    group_col: str | None = "symbol",
) -> pd.DataFrame:
    """Remove rows whose target window extends beyond the current partition.

    Labels are commonly calculated on the full time series before chronological
    partitioning. Without purging, the last ``h`` rows of an earlier partition
    can consume outcomes from the next partition. This helper removes those
    rows separately within each symbol.
    """
    horizon = target_forward_horizon(target)
    out = df.copy()
    if out.empty:
        return out

    if group_col and group_col in out.columns:
        from_end = out.groupby(group_col, sort=False).cumcount(ascending=False)
        return out.loc[from_end >= horizon].copy()
    if len(out) <= horizon:
        return out.iloc[0:0].copy()
    return out.iloc[:-horizon].copy()
