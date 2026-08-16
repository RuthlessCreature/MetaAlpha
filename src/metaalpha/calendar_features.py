from __future__ import annotations

import pandas as pd


def add_gregorian_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    out = df.copy()
    dt = pd.to_datetime(out[date_col], errors="raise")
    out["calendar__v1__weekday"] = dt.dt.weekday.astype("int8")
    out["calendar__v1__month"] = dt.dt.month.astype("int8")
    out["calendar__v1__quarter"] = dt.dt.quarter.astype("int8")
    out["calendar__v1__day_of_month"] = dt.dt.day.astype("int8")
    out["calendar__v1__is_month_start"] = dt.dt.is_month_start.astype("int8")
    out["calendar__v1__is_month_end"] = dt.dt.is_month_end.astype("int8")
    return out


class GanzhiEngineNotConfigured(RuntimeError):
    pass


def add_ganzhi_features(*args, **kwargs):
    """Reserved engine boundary for an ephemeris-backed Ganzhi implementation.

    v0.1 intentionally refuses to fabricate stem/branch values from an
    undocumented shortcut. The implementation must explicitly freeze:
    - timezone;
    - day-boundary convention;
    - solar-term convention for month/year transitions;
    - astronomical/calendar source and version.
    """
    raise GanzhiEngineNotConfigured(
        "Ganzhi engine is not configured. Register and document the calendrical convention before use."
    )
