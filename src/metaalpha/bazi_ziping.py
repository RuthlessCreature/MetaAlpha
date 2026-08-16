from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from .ganzhi import BRANCHES, STEMS, STEM_ELEMENT, STEM_POLARITY

HIDDEN_STEMS: dict[str, tuple[str, ...]] = {
    "子": ("癸",),
    "丑": ("己", "癸", "辛"),
    "寅": ("甲", "丙", "戊"),
    "卯": ("乙",),
    "辰": ("戊", "乙", "癸"),
    "巳": ("丙", "戊", "庚"),
    "午": ("丁", "己"),
    "未": ("己", "丁", "乙"),
    "申": ("庚", "壬", "戊"),
    "酉": ("辛",),
    "戌": ("戊", "辛", "丁"),
    "亥": ("壬", "甲"),
}

ELEMENT_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
ELEMENT_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

CLASHES = {frozenset(x) for x in (("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥"))}
HARMS = {frozenset(x) for x in (("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌"))}
BREAKS = {frozenset(x) for x in (("子", "酉"), ("丑", "辰"), ("寅", "亥"), ("卯", "午"), ("巳", "申"), ("未", "戌"))}
PAIR_PUNISHMENTS = {frozenset(x) for x in (("子", "卯"),)}
THREE_PUNISHMENTS = (frozenset(("寅", "巳", "申")), frozenset(("丑", "未", "戌")))
SELF_PUNISHMENTS = {"辰", "午", "酉", "亥"}

YANG_BLADE_BRANCH = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}

WEALTH = {"正财", "偏财"}
OFFICIAL = {"正官"}
KILLINGS = {"七杀"}
RESOURCE = {"正印", "偏印"}
OUTPUT = {"食神", "伤官"}


@dataclass(frozen=True)
class ZipingPattern:
    candidate: str
    month_primary_ten_god: str
    use_mode: str


def ten_god(day_master: str, other_stem: str) -> str:
    if day_master not in STEMS or other_stem not in STEMS:
        raise ValueError("day_master and other_stem must be heavenly stems")

    dm_e = STEM_ELEMENT[day_master]
    other_e = STEM_ELEMENT[other_stem]
    same_polarity = STEM_POLARITY[day_master] == STEM_POLARITY[other_stem]

    if other_e == dm_e:
        return "比肩" if same_polarity else "劫财"
    if ELEMENT_GENERATES[dm_e] == other_e:
        return "食神" if same_polarity else "伤官"
    if ELEMENT_CONTROLS[dm_e] == other_e:
        return "偏财" if same_polarity else "正财"
    if ELEMENT_CONTROLS[other_e] == dm_e:
        return "七杀" if same_polarity else "正官"
    if ELEMENT_GENERATES[other_e] == dm_e:
        return "偏印" if same_polarity else "正印"
    raise AssertionError("unreachable five-element relationship")


def pattern_from_month_command(day_master: str, month_branch: str) -> ZipingPattern:
    primary = HIDDEN_STEMS[month_branch][0]
    tg = ten_god(day_master, primary)

    if day_master in YANG_BLADE_BRANCH and YANG_BLADE_BRANCH[day_master] == month_branch:
        return ZipingPattern("阳刃格", tg, "逆用")
    if tg == "正官":
        return ZipingPattern("官格", tg, "顺用")
    if tg in WEALTH:
        return ZipingPattern("财格", tg, "顺用")
    if tg in RESOURCE:
        return ZipingPattern("印格", tg, "顺用")
    if tg == "食神":
        return ZipingPattern("食神格", tg, "顺用")
    if tg == "七杀":
        return ZipingPattern("七杀格", tg, "逆用")
    if tg == "伤官":
        return ZipingPattern("伤官格", tg, "逆用")
    return ZipingPattern("建禄月劫", tg, "逆用")


def _has_pair(relation: set[frozenset[str]], a: str, b: str) -> bool:
    return frozenset((a, b)) in relation


def _month_punished(month_branch: str, branches: Iterable[str]) -> bool:
    branches = tuple(branches)
    others = [b for b in branches if b != month_branch]
    if any(_has_pair(PAIR_PUNISHMENTS, month_branch, b) for b in others):
        return True
    branch_set = set(branches)
    if any(month_branch in tri and tri.issubset(branch_set) for tri in THREE_PUNISHMENTS):
        return True
    if month_branch in SELF_PUNISHMENTS and sum(1 for b in branches if b == month_branch) >= 2:
        return True
    return False


def _visible_ten_gods(day_master: str, stems: Iterable[str]) -> list[str]:
    return [ten_god(day_master, s) for s in stems if s != day_master]


def _strategy_flags(pattern: str, visible: set[str]) -> dict[str, int]:
    has_wealth = bool(visible & WEALTH)
    has_official = "正官" in visible
    has_killings = "七杀" in visible
    has_resource = bool(visible & RESOURCE)
    has_food = "食神" in visible
    has_hurting = "伤官" in visible
    has_output = has_food or has_hurting

    flags = {
        "zpzt__v1__has_visible_wealth": int(has_wealth),
        "zpzt__v1__has_visible_official": int(has_official),
        "zpzt__v1__has_visible_killings": int(has_killings),
        "zpzt__v1__has_visible_resource": int(has_resource),
        "zpzt__v1__has_visible_food": int(has_food),
        "zpzt__v1__has_visible_hurting": int(has_hurting),
        "zpzt__v1__has_visible_output": int(has_output),
    }

    flags.update({
        "zpzt__v1__route_official_wealth": int(pattern == "官格" and has_wealth),
        "zpzt__v1__route_official_resource": int(pattern == "官格" and has_resource),
        "zpzt__v1__route_wealth_output": int(pattern == "财格" and has_output),
        "zpzt__v1__route_wealth_official": int(pattern == "财格" and has_official),
        "zpzt__v1__route_resource_official_killings": int(pattern == "印格" and (has_official or has_killings)),
        "zpzt__v1__route_food_wealth": int(pattern == "食神格" and has_wealth),
        "zpzt__v1__route_food_controls_killings": int(pattern == "食神格" and has_food and has_killings),
        "zpzt__v1__route_killings_food_control": int(pattern == "七杀格" and has_food),
        "zpzt__v1__route_killings_resource_transform": int(pattern == "七杀格" and has_resource),
        "zpzt__v1__route_hurting_wealth": int(pattern == "伤官格" and has_wealth),
        "zpzt__v1__route_hurting_resource": int(pattern == "伤官格" and has_resource),
        "zpzt__v1__route_blade_official_killings": int(pattern == "阳刃格" and (has_official or has_killings)),
        "zpzt__v1__route_lujie_official": int(pattern == "建禄月劫" and has_official),
        "zpzt__v1__route_lujie_wealth_output": int(pattern == "建禄月劫" and has_wealth and has_output),
        "zpzt__v1__route_lujie_killings_control": int(pattern == "建禄月劫" and has_killings and has_food),
    })
    return flags


def features_from_pillars(year: str, month: str, day: str, time: str) -> dict[str, object]:
    pillars = (year, month, day, time)
    if any(len(p) != 2 for p in pillars):
        raise ValueError("pillars must be two-character stem-branch strings")

    stems = [p[0] for p in pillars]
    branches = [p[1] for p in pillars]
    if any(s not in STEMS for s in stems) or any(b not in BRANCHES for b in branches):
        raise ValueError("invalid heavenly stem or earthly branch")

    day_master = day[0]
    month_branch = month[1]
    pattern = pattern_from_month_command(day_master, month_branch)
    month_hidden = HIDDEN_STEMS[month_branch]
    visible_non_dm = {ten_god(day_master, s) for i, s in enumerate(stems) if i != 2}

    out: dict[str, object] = {
        "zpzt__v1__day_master": day_master,
        "zpzt__v1__month_command": month_branch,
        "zpzt__v1__month_primary_stem": month_hidden[0],
        "zpzt__v1__month_primary_ten_god": pattern.month_primary_ten_god,
        "zpzt__v1__pattern_candidate": pattern.candidate,
        "zpzt__v1__use_mode": pattern.use_mode,
        "zpzt__v1__month_hidden_stems": "".join(month_hidden),
        "zpzt__v1__month_hidden_count": len(month_hidden),
        "zpzt__v1__month_hidden_transmitted_count": sum(1 for s in month_hidden if s in (stems[0], stems[1], stems[3])),
        "zpzt__v1__month_clash": int(any(_has_pair(CLASHES, month_branch, b) for i, b in enumerate(branches) if i != 1)),
        "zpzt__v1__month_harm": int(any(_has_pair(HARMS, month_branch, b) for i, b in enumerate(branches) if i != 1)),
        "zpzt__v1__month_break": int(any(_has_pair(BREAKS, month_branch, b) for i, b in enumerate(branches) if i != 1)),
        "zpzt__v1__month_punishment": int(_month_punished(month_branch, branches)),
    }

    for pos, stem in zip(("year", "month", "time"), (stems[0], stems[1], stems[3])):
        out[f"zpzt__v1__{pos}_stem_ten_god"] = ten_god(day_master, stem)

    for pos, branch in zip(("year", "month", "day", "time"), branches):
        hidden = HIDDEN_STEMS[branch]
        out[f"zpzt__v1__{pos}_branch_hidden_ten_gods"] = "|".join(ten_god(day_master, s) for s in hidden)

    out.update(_strategy_flags(pattern.candidate, visible_non_dm))
    out["zpzt__v1__route_hit_count"] = sum(
        int(v) for k, v in out.items() if k.startswith("zpzt__v1__route_")
    )
    out["zpzt__v1__month_disruption_count"] = sum(
        int(out[k]) for k in (
            "zpzt__v1__month_clash",
            "zpzt__v1__month_harm",
            "zpzt__v1__month_break",
            "zpzt__v1__month_punishment",
        )
    )
    return out


def add_ziping_features(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "ganzhi__v2__year_pillar",
        "ganzhi__v2__month_pillar",
        "ganzhi__v2__day_pillar",
        "ganzhi__v2__time_pillar",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Ganzhi features required before Ziping features: {missing}")

    rows = [
        features_from_pillars(y, m, d, t)
        for y, m, d, t in zip(*(df[c] for c in required))
    ]
    feat = pd.DataFrame(rows, index=df.index)
    return pd.concat([df.copy(), feat], axis=1)
