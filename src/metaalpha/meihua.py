from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from lunar_python import Solar

from .ganzhi import BRANCHES, _market_anchor


TRIGRAM_ORDER = ("乾", "兑", "离", "震", "巽", "坎", "艮", "坤")
TRIGRAM_BY_NUMBER = {i + 1: name for i, name in enumerate(TRIGRAM_ORDER)}
TRIGRAM_LINES = {
    # bottom -> top, yang=1 / yin=0
    "乾": (1, 1, 1),
    "兑": (1, 1, 0),
    "离": (1, 0, 1),
    "震": (1, 0, 0),
    "巽": (0, 1, 1),
    "坎": (0, 1, 0),
    "艮": (0, 0, 1),
    "坤": (0, 0, 0),
}
TRIGRAM_FROM_LINES = {v: k for k, v in TRIGRAM_LINES.items()}
TRIGRAM_ELEMENT = {
    "乾": "金",
    "兑": "金",
    "离": "火",
    "震": "木",
    "巽": "木",
    "坎": "水",
    "艮": "土",
    "坤": "土",
}
BRANCH_NUMBER = {branch: i + 1 for i, branch in enumerate(BRANCHES)}

_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _mod_or_max(value: int, modulus: int) -> int:
    rem = value % modulus
    return modulus if rem == 0 else rem


def _element_relation(body: str, use: str) -> str:
    if body == use:
        return "比和"
    if _GENERATES[body] == use:
        return "体生用"
    if _GENERATES[use] == body:
        return "用生体"
    if _CONTROLS[body] == use:
        return "体克用"
    if _CONTROLS[use] == body:
        return "用克体"
    raise ValueError(f"unresolved element relation: {body}/{use}")


@dataclass(frozen=True)
class MeihuaPlate:
    lunar_year_branch: str
    lunar_month: int
    lunar_day: int
    time_branch: str
    upper_trigram: str
    lower_trigram: str
    moving_line: int
    changed_upper_trigram: str
    changed_lower_trigram: str
    mutual_upper_trigram: str
    mutual_lower_trigram: str
    body_trigram: str
    use_trigram: str

    @property
    def base_lines(self) -> tuple[int, ...]:
        return TRIGRAM_LINES[self.lower_trigram] + TRIGRAM_LINES[self.upper_trigram]

    @property
    def changed_lines(self) -> tuple[int, ...]:
        return TRIGRAM_LINES[self.changed_lower_trigram] + TRIGRAM_LINES[self.changed_upper_trigram]


def plate_for_datetime(value, anchor_hour: int = 9, anchor_minute: int = 25) -> MeihuaPlate:
    """Freeze the traditional lunar year-month-day-hour Meihua time method.

    Convention registered in META_FWD_001:
    - lunar-year earthly branch ordinal 子1..亥12;
    - absolute lunar month number (leap month shares ordinary month number);
    - lunar day number;
    - earthly-branch ordinal of the clock time;
    - Earlier-Heaven trigram order 乾1兑2离3震4巽5坎6艮7坤8;
    - zero remainder maps to 8 for trigrams and 6 for moving line.
    """
    dt = _market_anchor(value, anchor_hour, anchor_minute)
    lunar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second).getLunar()

    year_branch = lunar.getYearZhi()
    lunar_month = abs(int(lunar.getMonth()))
    lunar_day = int(lunar.getDay())
    # Use the same civil-hour branch convention as the library, but the branch
    # ordinal is frozen independently for the Meihua arithmetic.
    time_branch = lunar.getTimeZhi()
    year_number = BRANCH_NUMBER[year_branch]
    time_number = BRANCH_NUMBER[time_branch]

    ymd_sum = year_number + lunar_month + lunar_day
    total = ymd_sum + time_number
    upper = TRIGRAM_BY_NUMBER[_mod_or_max(ymd_sum, 8)]
    lower = TRIGRAM_BY_NUMBER[_mod_or_max(total, 8)]
    moving_line = _mod_or_max(total, 6)

    lines = list(TRIGRAM_LINES[lower] + TRIGRAM_LINES[upper])
    changed = lines.copy()
    changed[moving_line - 1] = 1 - changed[moving_line - 1]
    changed_lower = TRIGRAM_FROM_LINES[tuple(changed[:3])]
    changed_upper = TRIGRAM_FROM_LINES[tuple(changed[3:])]

    # Mutual hexagram: original lines 2-4 form lower mutual, 3-5 upper mutual.
    mutual_lower = TRIGRAM_FROM_LINES[tuple(lines[1:4])]
    mutual_upper = TRIGRAM_FROM_LINES[tuple(lines[2:5])]

    moving_trigram = "lower" if moving_line <= 3 else "upper"
    if moving_trigram == "lower":
        use = lower
        body = upper
    else:
        use = upper
        body = lower

    return MeihuaPlate(
        lunar_year_branch=year_branch,
        lunar_month=lunar_month,
        lunar_day=lunar_day,
        time_branch=time_branch,
        upper_trigram=upper,
        lower_trigram=lower,
        moving_line=moving_line,
        changed_upper_trigram=changed_upper,
        changed_lower_trigram=changed_lower,
        mutual_upper_trigram=mutual_upper,
        mutual_lower_trigram=mutual_lower,
        body_trigram=body,
        use_trigram=use,
    )


def features_for_datetime(value, anchor_hour: int = 9, anchor_minute: int = 25) -> dict[str, object]:
    p = plate_for_datetime(value, anchor_hour, anchor_minute)
    body_element = TRIGRAM_ELEMENT[p.body_trigram]
    use_element = TRIGRAM_ELEMENT[p.use_trigram]
    base_lines = "".join(str(x) for x in p.base_lines)
    changed_lines = "".join(str(x) for x in p.changed_lines)
    return {
        "meihua__v1__lunar_year_branch": p.lunar_year_branch,
        "meihua__v1__lunar_month": p.lunar_month,
        "meihua__v1__lunar_day": p.lunar_day,
        "meihua__v1__time_branch": p.time_branch,
        "meihua__v1__upper_trigram": p.upper_trigram,
        "meihua__v1__lower_trigram": p.lower_trigram,
        "meihua__v1__base_hexagram_key": f"{p.upper_trigram}/{p.lower_trigram}",
        "meihua__v1__base_line_pattern": base_lines,
        "meihua__v1__moving_line": p.moving_line,
        "meihua__v1__moving_trigram": "lower" if p.moving_line <= 3 else "upper",
        "meihua__v1__changed_upper_trigram": p.changed_upper_trigram,
        "meihua__v1__changed_lower_trigram": p.changed_lower_trigram,
        "meihua__v1__changed_hexagram_key": f"{p.changed_upper_trigram}/{p.changed_lower_trigram}",
        "meihua__v1__changed_line_pattern": changed_lines,
        "meihua__v1__mutual_upper_trigram": p.mutual_upper_trigram,
        "meihua__v1__mutual_lower_trigram": p.mutual_lower_trigram,
        "meihua__v1__mutual_hexagram_key": f"{p.mutual_upper_trigram}/{p.mutual_lower_trigram}",
        "meihua__v1__body_trigram": p.body_trigram,
        "meihua__v1__use_trigram": p.use_trigram,
        "meihua__v1__body_element": body_element,
        "meihua__v1__use_element": use_element,
        "meihua__v1__body_use_relation": _element_relation(body_element, use_element),
        "meihua__v1__fortune_score_defined": 0,
    }


def add_meihua_features(
    df: pd.DataFrame,
    date_col: str = "date",
    anchor_hour: int = 9,
    anchor_minute: int = 25,
) -> pd.DataFrame:
    out = df.copy()
    feat = pd.DataFrame(
        [features_for_datetime(v, anchor_hour, anchor_minute) for v in out[date_col]],
        index=out.index,
    )
    return pd.concat([out, feat], axis=1)
