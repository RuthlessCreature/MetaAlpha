from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from lunar_python import Solar

TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")

STEMS = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
JIAZI = tuple(STEMS[i % 10] + BRANCHES[i % 12] for i in range(60))
JIAZI_INDEX = {v: i for i, v in enumerate(JIAZI)}

STEM_ELEMENT = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

STEM_POLARITY = {
    "甲": "阳", "乙": "阴",
    "丙": "阳", "丁": "阴",
    "戊": "阳", "己": "阴",
    "庚": "阳", "辛": "阴",
    "壬": "阳", "癸": "阴",
}

BRANCH_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

BRANCH_POLARITY = {
    "子": "阳", "丑": "阴", "寅": "阳", "卯": "阴",
    "辰": "阳", "巳": "阴", "午": "阳", "未": "阴",
    "申": "阳", "酉": "阴", "戌": "阳", "亥": "阴",
}


@dataclass(frozen=True)
class Pillars:
    year: str
    month: str
    day: str
    time: str
    jieqi: str | None = None

    @property
    def year_stem(self) -> str:
        return self.year[0]

    @property
    def year_branch(self) -> str:
        return self.year[1]

    @property
    def month_stem(self) -> str:
        return self.month[0]

    @property
    def month_branch(self) -> str:
        return self.month[1]

    @property
    def day_stem(self) -> str:
        return self.day[0]

    @property
    def day_branch(self) -> str:
        return self.day[1]

    @property
    def time_stem(self) -> str:
        return self.time[0]

    @property
    def time_branch(self) -> str:
        return self.time[1]


def _market_anchor(value, hour: int = 9, minute: int = 25) -> datetime:
    """Convert a date-like value to the registered A-share research anchor.

    A date-only or midnight value is interpreted as that civil date at the
    configured market anchor in Asia/Shanghai. A timestamp with a non-zero time
    keeps its clock time. A timezone-aware timestamp is converted to Shanghai.
    """
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize(TZ_SHANGHAI)
    else:
        ts = ts.tz_convert(TZ_SHANGHAI)

    if ts.hour == 0 and ts.minute == 0 and ts.second == 0 and ts.microsecond == 0:
        ts = ts.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return ts.to_pydatetime()


def pillars_from_datetime(value, anchor_hour: int = 9, anchor_minute: int = 25) -> Pillars:
    dt = _market_anchor(value, anchor_hour, anchor_minute)
    solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    lunar = solar.getLunar()
    eight = lunar.getEightChar()
    jieqi = lunar.getJieQi()
    return Pillars(
        year=eight.getYear(),
        month=eight.getMonth(),
        day=eight.getDay(),
        time=eight.getTime(),
        jieqi=jieqi if jieqi else None,
    )


def _pillar_features(prefix: str, pillar: str) -> dict[str, object]:
    stem, branch = pillar[0], pillar[1]
    return {
        f"ganzhi__v2__{prefix}_pillar": pillar,
        f"ganzhi__v2__{prefix}_stem": stem,
        f"ganzhi__v2__{prefix}_branch": branch,
        f"ganzhi__v2__{prefix}_stem_element": STEM_ELEMENT[stem],
        f"ganzhi__v2__{prefix}_stem_polarity": STEM_POLARITY[stem],
        f"ganzhi__v2__{prefix}_branch_element": BRANCH_ELEMENT[branch],
        f"ganzhi__v2__{prefix}_branch_polarity": BRANCH_POLARITY[branch],
        f"ganzhi__v2__{prefix}_jiazi_index": JIAZI_INDEX[pillar],
    }


def features_for_datetime(value, anchor_hour: int = 9, anchor_minute: int = 25) -> dict[str, object]:
    p = pillars_from_datetime(value, anchor_hour, anchor_minute)
    out: dict[str, object] = {}
    out.update(_pillar_features("year", p.year))
    out.update(_pillar_features("month", p.month))
    out.update(_pillar_features("day", p.day))
    out.update(_pillar_features("time", p.time))
    out["ganzhi__v2__jieqi"] = p.jieqi or ""
    out["ganzhi__v2__day_master"] = p.day_stem
    return out


def add_ganzhi_features(
    df: pd.DataFrame,
    date_col: str = "date",
    anchor_hour: int = 9,
    anchor_minute: int = 25,
) -> pd.DataFrame:
    out = df.copy()
    rows = [
        features_for_datetime(v, anchor_hour=anchor_hour, anchor_minute=anchor_minute)
        for v in out[date_col]
    ]
    feat = pd.DataFrame(rows, index=out.index)
    return pd.concat([out, feat], axis=1)
