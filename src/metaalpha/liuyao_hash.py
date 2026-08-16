from __future__ import annotations

import hashlib

import pandas as pd


_SALT = "METAALPHA|LIUYAO_HASH_V1|NEGATIVE_CONTROL|2026-08-16"
_LINE_VALUES = (6, 7, 8, 9)  # old yin, young yang, young yin, old yang


def _base_yang(value: int) -> int:
    return 1 if value in (7, 9) else 0


def _changed_yang(value: int) -> int:
    if value == 6:
        return 1
    if value == 9:
        return 0
    return _base_yang(value)


def features_for_date(value) -> dict[str, object]:
    """Deterministic pseudo-random six-line negative control.

    This is intentionally *not* a traditional divination algorithm. It hashes
    only the civil target date plus a frozen salt, then maps six digest bytes to
    6/7/8/9 line states. Its role is to detect whether a similarly structured
    but semantically meaningless symbolic state can appear predictive.
    """
    date = pd.Timestamp(value).normalize().strftime("%Y-%m-%d")
    digest = hashlib.sha256(f"{_SALT}|{date}|09:25:00+08:00".encode("utf-8")).digest()
    lines = tuple(_LINE_VALUES[b % 4] for b in digest[:6])  # bottom -> top
    base = tuple(_base_yang(v) for v in lines)
    changed = tuple(_changed_yang(v) for v in lines)
    moving = tuple(i + 1 for i, v in enumerate(lines) if v in (6, 9))
    return {
        "liuyao_hash__v1__base_pattern": "".join(str(x) for x in base),
        "liuyao_hash__v1__changed_pattern": "".join(str(x) for x in changed),
        "liuyao_hash__v1__moving_count": len(moving),
        "liuyao_hash__v1__moving_lines_key": "-".join(str(x) for x in moving) if moving else "none",
        "liuyao_hash__v1__line_state_key": "-".join(str(x) for x in lines),
        "liuyao_hash__v1__negative_control": 1,
    }


def add_liuyao_hash_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    out = df.copy()
    feat = pd.DataFrame([features_for_date(v) for v in out[date_col]], index=out.index)
    return pd.concat([out, feat], axis=1)
