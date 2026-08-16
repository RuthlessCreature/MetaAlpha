from __future__ import annotations

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
    """Create leakage-safe forward labels from close prices.

    Rows must already be sorted chronologically within each symbol. The
    function sorts defensively when `group_col` and `date` are available.
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

    # Future realized volatility uses only future one-session returns t+1..t+h.
    for h in (5, 20):
        if group_col and group_col in out.columns:
            out[f"vol_fwd_{h}"] = out.groupby(group_col, sort=False)["ret_1"].transform(
                lambda s: s.shift(-h).rolling(h, min_periods=h).std().shift(h - 1)
            )
        else:
            out[f"vol_fwd_{h}"] = (
                out["ret_1"].shift(-h).rolling(h, min_periods=h).std().shift(h - 1)
            )

    return out
