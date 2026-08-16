from __future__ import annotations

import pandas as pd

from .bazi_ziping import ELEMENT_CONTROLS, ELEMENT_GENERATES, HIDDEN_STEMS, ten_god
from .ganzhi import BRANCH_ELEMENT, STEM_ELEMENT


def _element_relation(day_element: str, other_element: str) -> str:
    if day_element == other_element:
        return "same"
    if ELEMENT_GENERATES[other_element] == day_element:
        return "resource"
    if ELEMENT_GENERATES[day_element] == other_element:
        return "output"
    if ELEMENT_CONTROLS[day_element] == other_element:
        return "wealth"
    if ELEMENT_CONTROLS[other_element] == day_element:
        return "official_killings"
    raise AssertionError("unreachable five-element relationship")


def strength_primitives_from_pillars(year: str, month: str, day: str, time: str) -> dict[str, object]:
    stems = [year[0], month[0], day[0], time[0]]
    branches = [year[1], month[1], day[1], time[1]]
    dm = day[0]
    dm_element = STEM_ELEMENT[dm]
    month_element = BRANCH_ELEMENT[month[1]]

    exact_root_count = sum(dm in HIDDEN_STEMS[b] for b in branches)
    same_element_hidden_count = sum(
        1
        for b in branches
        for hs in HIDDEN_STEMS[b]
        if STEM_ELEMENT[hs] == dm_element
    )
    resource_hidden_count = sum(
        1
        for b in branches
        for hs in HIDDEN_STEMS[b]
        if ELEMENT_GENERATES[STEM_ELEMENT[hs]] == dm_element
    )

    visible_tg = [ten_god(dm, stems[i]) for i in (0, 1, 3)]
    visible_support_count = sum(tg in {"比肩", "劫财", "正印", "偏印"} for tg in visible_tg)
    visible_drain_count = sum(tg in {"食神", "伤官", "正财", "偏财", "正官", "七杀"} for tg in visible_tg)

    month_relation = _element_relation(dm_element, month_element)
    return {
        "zpzt_strength__v1__day_master_element": dm_element,
        "zpzt_strength__v1__month_element": month_element,
        "zpzt_strength__v1__month_relation": month_relation,
        "zpzt_strength__v1__month_supports_daymaster": int(month_relation in {"same", "resource"}),
        "zpzt_strength__v1__exact_root_count": int(exact_root_count),
        "zpzt_strength__v1__same_element_hidden_count": int(same_element_hidden_count),
        "zpzt_strength__v1__resource_hidden_count": int(resource_hidden_count),
        "zpzt_strength__v1__visible_support_count": int(visible_support_count),
        "zpzt_strength__v1__visible_drain_count": int(visible_drain_count),
        # Deliberately no aggregate strong/weak score in v1.
        "zpzt_strength__v1__aggregate_score_defined": 0,
    }


def add_ziping_strength_primitives(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "ganzhi__v2__year_pillar",
        "ganzhi__v2__month_pillar",
        "ganzhi__v2__day_pillar",
        "ganzhi__v2__time_pillar",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Ganzhi features required before strength primitives: {missing}")

    rows = [
        strength_primitives_from_pillars(y, m, d, t)
        for y, m, d, t in zip(*(df[c] for c in required))
    ]
    feat = pd.DataFrame(rows, index=df.index)
    return pd.concat([df.copy(), feat], axis=1)
