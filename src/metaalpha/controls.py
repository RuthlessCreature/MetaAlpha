from __future__ import annotations

import hashlib
import pandas as pd


def _stable_bucket(value: str, modulo: int, salt: str) -> int:
    payload = f"{salt}|{value}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") % modulo


def add_deterministic_null_controls(
    df: pd.DataFrame,
    *,
    date_col: str = "date",
    salt: str = "metaalpha-v1",
) -> pd.DataFrame:
    """Add reproducible pseudo-random labels independent of market outcomes."""
    out = df.copy()
    dates = pd.to_datetime(out[date_col], errors="raise").dt.strftime("%Y-%m-%d")
    out["control__v1__random_stem"] = [
        _stable_bucket(d, 10, f"{salt}:stem") for d in dates
    ]
    out["control__v1__random_branch"] = [
        _stable_bucket(d, 12, f"{salt}:branch") for d in dates
    ]
    out["control__v1__random_jiazi"] = [
        _stable_bucket(d, 60, f"{salt}:jiazi") for d in dates
    ]
    return out


def add_shifted_feature(
    df: pd.DataFrame,
    source_col: str,
    *,
    shift_rows: int,
    group_col: str | None = "symbol",
) -> pd.DataFrame:
    """Create a row-shifted null feature without wrapping values across edges."""
    if shift_rows == 0:
        raise ValueError("shift_rows must be non-zero for a null control")
    out = df.copy()
    target = f"control__v1__shift_{shift_rows}__{source_col}"
    if group_col and group_col in out.columns:
        out[target] = out.groupby(group_col, sort=False)[source_col].shift(shift_rows)
    else:
        out[target] = out[source_col].shift(shift_rows)
    return out
