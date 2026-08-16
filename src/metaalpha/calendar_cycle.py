from __future__ import annotations

from datetime import datetime
from math import cos, pi, sin
from zoneinfo import ZoneInfo

import pandas as pd
from lunar_python import Solar

from .ganzhi import JIAZI_INDEX, pillars_from_datetime


TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")
JIE_QI_ORDER = (
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
)
JIE_QI_INDEX = {name: i for i, name in enumerate(JIE_QI_ORDER)}
JIE_QI_ALIASES = {
    "DA_XUE": "大雪",
    "DONG_ZHI": "冬至",
    "XIAO_HAN": "小寒",
    "DA_HAN": "大寒",
    "LI_CHUN": "立春",
    "YU_SHUI": "雨水",
    "JING_ZHE": "惊蛰",
}


def _anchor(value, hour: int = 9, minute: int = 25) -> datetime:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize(TZ_SHANGHAI)
    else:
        ts = ts.tz_convert(TZ_SHANGHAI)
    if ts.hour == 0 and ts.minute == 0 and ts.second == 0 and ts.microsecond == 0:
        ts = ts.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return ts.to_pydatetime()


def _solar_to_datetime(solar) -> datetime:
    return datetime(
        solar.getYear(),
        solar.getMonth(),
        solar.getDay(),
        solar.getHour(),
        solar.getMinute(),
        solar.getSecond(),
        tzinfo=TZ_SHANGHAI,
    )


def _canonical_jieqi_name(name: str) -> str:
    canonical = JIE_QI_ALIASES.get(name, name)
    if canonical not in JIE_QI_INDEX:
        raise ValueError(f"unregistered solar-term name from lunar_python: {name!r}")
    return canonical


def cycle_features_for_datetime(value, anchor_hour: int = 9, anchor_minute: int = 25) -> dict[str, object]:
    """Return deterministic Chinese-calendar cycle features at the market anchor.

    Solar-term phase is calculated from the exact previous/next term timestamps
    returned by the frozen calendar engine. It is a normalized interval phase,
    not an arbitrary day-count bucket.
    """
    dt = _anchor(value, anchor_hour, anchor_minute)
    lunar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second).getLunar()
    prev_jq = lunar.getPrevJieQi()
    next_jq = lunar.getNextJieQi()
    if prev_jq is None or next_jq is None:
        raise ValueError(f"solar-term neighbors unavailable for {dt.isoformat()}")

    prev_name = _canonical_jieqi_name(prev_jq.getName())
    next_name = _canonical_jieqi_name(next_jq.getName())
    prev_dt = _solar_to_datetime(prev_jq.getSolar())
    next_dt = _solar_to_datetime(next_jq.getSolar())
    interval_seconds = (next_dt - prev_dt).total_seconds()
    if interval_seconds <= 0:
        raise ValueError(f"non-positive solar-term interval: {prev_dt} -> {next_dt}")
    phase = (dt - prev_dt).total_seconds() / interval_seconds
    # Calendar-engine boundary precision can create machine-sized excursions.
    phase = max(0.0, min(1.0, float(phase)))
    quartile = min(3, int(phase * 4.0))

    pillars = pillars_from_datetime(dt, anchor_hour=anchor_hour, anchor_minute=anchor_minute)
    day_index = JIAZI_INDEX[pillars.day]
    term_index = JIE_QI_INDEX[prev_name]
    angle = 2.0 * pi * (term_index + phase) / 24.0

    return {
        "cycle__v1__prev_jieqi": prev_name,
        "cycle__v1__next_jieqi": next_name,
        "cycle__v1__prev_jieqi_index": term_index,
        "cycle__v1__jieqi_phase": phase,
        "cycle__v1__jieqi_phase_quartile": quartile,
        "cycle__v1__jieqi_half": 0 if phase < 0.5 else 1,
        "cycle__v1__jie_or_qi": "qi" if term_index % 2 == 0 else "jie",
        "cycle__v1__term_phase_sin": sin(angle),
        "cycle__v1__term_phase_cos": cos(angle),
        "cycle__v1__day_pillar": pillars.day,
        "cycle__v1__day_stem": pillars.day_stem,
        "cycle__v1__day_branch": pillars.day_branch,
        "cycle__v1__day_jiazi_index": day_index,
        "cycle__v1__day_cycle_decade": day_index // 10,
        "cycle__v1__month_stem": pillars.month_stem,
        "cycle__v1__month_branch": pillars.month_branch,
    }


def add_calendar_cycle_features(
    df: pd.DataFrame,
    *,
    date_col: str = "date",
    anchor_hour: int = 9,
    anchor_minute: int = 25,
) -> pd.DataFrame:
    out = df.copy()
    rows = [
        cycle_features_for_datetime(v, anchor_hour=anchor_hour, anchor_minute=anchor_minute)
        for v in out[date_col]
    ]
    feat = pd.DataFrame(rows, index=out.index)
    return pd.concat([out, feat], axis=1)
