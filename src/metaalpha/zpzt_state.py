from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .bazi_ziping import (
    HIDDEN_STEMS,
    KILLINGS,
    OFFICIAL,
    OUTPUT,
    RESOURCE,
    WEALTH,
    features_from_pillars as primitive_features_from_pillars,
    ten_god,
)
from .ganzhi import BRANCH_ELEMENT, STEM_ELEMENT

STEM_COMBINATIONS = {
    frozenset(("甲", "己")),
    frozenset(("乙", "庚")),
    frozenset(("丙", "辛")),
    frozenset(("丁", "壬")),
    frozenset(("戊", "癸")),
}

BRANCH_SIX_COMBINATIONS = {
    frozenset(("子", "丑")),
    frozenset(("寅", "亥")),
    frozenset(("卯", "戌")),
    frozenset(("辰", "酉")),
    frozenset(("巳", "申")),
    frozenset(("午", "未")),
}

BRANCH_THREE_COMBINATIONS = {
    frozenset(("申", "子", "辰")),
    frozenset(("亥", "卯", "未")),
    frozenset(("寅", "午", "戌")),
    frozenset(("巳", "酉", "丑")),
}


@dataclass(frozen=True)
class ProvisionalState:
    formation: bool
    failure: bool
    rescue: bool
    requires_strength: bool
    state: str
    reasons: tuple[str, ...]


def _is_combined(stem: str, stems: list[str]) -> bool:
    return any(frozenset((stem, other)) in STEM_COMBINATIONS for other in stems if other != stem)


def _month_has_branch_combination(month_branch: str, branches: list[str]) -> bool:
    for other in branches:
        if other != month_branch and frozenset((month_branch, other)) in BRANCH_SIX_COMBINATIONS:
            return True
    branch_set = set(branches)
    return any(month_branch in tri and tri.issubset(branch_set) for tri in BRANCH_THREE_COMBINATIONS)


def _visible_context(year: str, month: str, day: str, time: str) -> dict[str, object]:
    stems = [year[0], month[0], day[0], time[0]]
    branches = [year[1], month[1], day[1], time[1]]
    dm = day[0]
    visible_positions = [(0, year[0]), (1, month[0]), (3, time[0])]
    visible_tg = [(pos, stem, ten_god(dm, stem)) for pos, stem in visible_positions]
    visible_labels = {tg for _, _, tg in visible_tg}

    killing_stems = [s for _, s, tg in visible_tg if tg == "七杀"]
    hurting_stems = [s for _, s, tg in visible_tg if tg == "伤官"]
    wealth_stems = [s for _, s, tg in visible_tg if tg in WEALTH]
    resource_stems = [s for _, s, tg in visible_tg if tg in RESOURCE]
    all_hidden = {hs for b in branches for hs in HIDDEN_STEMS[b]}

    return {
        "stems": stems,
        "branches": branches,
        "dm": dm,
        "visible_labels": visible_labels,
        "has_wealth": bool(visible_labels & WEALTH),
        "has_official": bool(visible_labels & OFFICIAL),
        "has_killings": bool(visible_labels & KILLINGS),
        "has_resource": bool(visible_labels & RESOURCE),
        "has_food": "食神" in visible_labels,
        "has_hurting": "伤官" in visible_labels,
        "has_output": bool(visible_labels & OUTPUT),
        "has_peer": bool(visible_labels & {"比肩", "劫财"}),
        "has_robwealth": "劫财" in visible_labels,
        "has_indirect_resource": "偏印" in visible_labels,
        "killing_combined": any(_is_combined(s, stems) for s in killing_stems),
        "hurting_combined": any(_is_combined(s, stems) for s in hurting_stems),
        "wealth_combined": any(_is_combined(s, stems) for s in wealth_stems),
        "resource_rooted": any(s in all_hidden for s in resource_stems),
        "month_has_combination": _month_has_branch_combination(month[1], branches),
    }


def evaluate_provisional_state(year: str, month: str, day: str, time: str) -> ProvisionalState:
    base = primitive_features_from_pillars(year, month, day, time)
    c = _visible_context(year, month, day, time)
    pattern = str(base["zpzt__v1__pattern_candidate"])
    disrupted = bool(base["zpzt__v1__month_disruption_count"])

    formation = False
    failure = False
    rescue = False
    requires_strength = False
    reasons: list[str] = []

    if pattern == "官格":
        formation = (c["has_wealth"] or c["has_resource"]) and not disrupted
        failure = c["has_hurting"] or disrupted
        rescue = (c["has_hurting"] and c["has_resource"]) or (disrupted and c["month_has_combination"])
        if formation:
            reasons.append("官逢财印且月令未见已编码刑冲破害")
        if failure:
            reasons.append("官见伤或月令结构受扰")
        if rescue:
            reasons.append("官格败象见印制伤或会合解结构扰动候选")

    elif pattern == "财格":
        formation = c["has_official"] or c["has_output"]
        failure = c["has_killings"]
        requires_strength = c["has_output"] or c["has_peer"]
        rescue = (c["has_robwealth"] and (c["has_food"] or c["has_official"])) or (
            c["has_killings"] and (c["has_food"] or c["killing_combined"])
        )
        if formation:
            reasons.append("财见官或食伤生财路线")
        if failure:
            reasons.append("财透七杀败象候选")
        if requires_strength:
            reasons.append("财轻比重/身强等条件尚需强弱层")
        if rescue:
            reasons.append("财逢劫见食官或七杀受制/被合候选")

    elif pattern == "印格":
        formation = c["has_official"] or c["has_killings"]
        failure = c["has_wealth"]
        requires_strength = True
        rescue = c["has_wealth"] and c["has_robwealth"]
        if formation:
            reasons.append("印见官杀相生路线")
        if failure:
            reasons.append("印逢财为败象候选，轻重待强弱层确认")
        if rescue:
            reasons.append("印逢财而见劫财解救候选")

    elif pattern == "食神格":
        formation = c["has_wealth"] or (c["has_killings"] and c["has_resource"] and not c["has_wealth"])
        failure = c["has_indirect_resource"] or (c["has_wealth"] and c["has_killings"])
        rescue = c["has_indirect_resource"] and (c["has_killings"] or c["has_wealth"])
        if formation:
            reasons.append("食神生财或食带杀透印路线")
        if failure:
            reasons.append("食神逢枭或生财露杀败象")
        if rescue:
            reasons.append("食逢枭而就杀或生财护食候选")

    elif pattern == "七杀格":
        formation = c["has_food"]
        failure = c["has_wealth"] and not c["has_food"]
        requires_strength = True
        rescue = c["has_food"] and c["has_resource"] and c["has_wealth"]
        if formation:
            reasons.append("七杀见食神制伏候选，身强条件待确认")
        if failure:
            reasons.append("七杀逢财无制败象")
        if rescue:
            reasons.append("杀逢食制、印来护杀、财去印存食候选")

    elif pattern == "伤官格":
        gold_water_hurting = STEM_ELEMENT[day[0]] == "金" and BRANCH_ELEMENT[month[1]] == "水"
        formation = c["has_wealth"] or c["has_resource"]
        failure = (c["has_official"] and not gold_water_hurting) or (c["has_wealth"] and c["has_killings"])
        requires_strength = c["has_resource"] or (c["has_wealth"] and c["has_killings"])
        rescue = c["has_wealth"] and c["has_killings"] and c["killing_combined"]
        if formation:
            reasons.append("伤官生财或佩印路线")
        if failure:
            reasons.append("伤官见官（非金水）或生财带杀败象候选")
        if rescue:
            reasons.append("伤官生财透杀而杀被合候选")

    elif pattern == "阳刃格":
        formation = (c["has_official"] or c["has_killings"]) and (c["has_wealth"] or c["has_resource"]) and not c["has_hurting"]
        failure = not (c["has_official"] or c["has_killings"])
        rescue = (c["has_official"] or c["has_killings"]) and c["has_output"] and c["has_resource"]
        if formation:
            reasons.append("阳刃透官杀、露财印且不见伤官候选")
        if failure:
            reasons.append("阳刃无官杀败象")
        if rescue:
            reasons.append("刃用官杀带食伤而见印护候选")

    elif pattern == "建禄月劫":
        formation = (
            (c["has_official"] and (c["has_wealth"] or c["has_resource"]))
            or (c["has_wealth"] and c["has_output"])
            or (c["has_killings"] and c["has_food"])
        )
        failure = (not c["has_wealth"] and not c["has_official"] and c["has_killings"] and c["has_resource"])
        rescue = (c["has_official"] and c["has_hurting"] and c["hurting_combined"]) or (
            c["has_wealth"] and c["has_killings"] and c["killing_combined"]
        )
        if formation:
            reasons.append("建禄月劫透官配财印、透财配食伤或透杀见制候选")
        if failure:
            reasons.append("建禄月劫无财官而透杀印败象")
        if rescue:
            reasons.append("建禄月劫官伤/财杀结构中忌神被合候选")

    if failure and rescue:
        state = "败中有救候选"
    elif formation and failure:
        state = "成中带忌候选"
    elif formation:
        state = "成候选"
    elif failure:
        state = "败候选"
    else:
        state = "未决"

    if requires_strength:
        state += "_待强弱层"

    return ProvisionalState(
        formation=formation,
        failure=failure,
        rescue=rescue,
        requires_strength=requires_strength,
        state=state,
        reasons=tuple(reasons),
    )


def state_features_from_pillars(year: str, month: str, day: str, time: str) -> dict[str, object]:
    s = evaluate_provisional_state(year, month, day, time)
    return {
        "zpzt_state__v1__formation_hit": int(s.formation),
        "zpzt_state__v1__failure_hit": int(s.failure),
        "zpzt_state__v1__rescue_hit": int(s.rescue),
        "zpzt_state__v1__requires_strength": int(s.requires_strength),
        "zpzt_state__v1__state": s.state,
        "zpzt_state__v1__reason_count": len(s.reasons),
        "zpzt_state__v1__reasons": "|".join(s.reasons),
    }


def add_ziping_state_features(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "ganzhi__v2__year_pillar",
        "ganzhi__v2__month_pillar",
        "ganzhi__v2__day_pillar",
        "ganzhi__v2__time_pillar",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Ganzhi features required before Ziping state features: {missing}")

    rows = [
        state_features_from_pillars(y, m, d, t)
        for y, m, d, t in zip(*(df[c] for c in required))
    ]
    feat = pd.DataFrame(rows, index=df.index)
    return pd.concat([df.copy(), feat], axis=1)
