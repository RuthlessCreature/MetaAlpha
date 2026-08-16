from __future__ import annotations

import pandas as pd

from .bazi_ziping import HIDDEN_STEMS, YANG_BLADE_BRANCH, ten_god
from .ganzhi import STEM_ELEMENT

THREE_HARMONY_ELEMENT: dict[frozenset[str], str] = {
    frozenset(("申", "子", "辰")): "水",
    frozenset(("亥", "卯", "未")): "木",
    frozenset(("寅", "午", "戌")): "火",
    frozenset(("巳", "酉", "丑")): "金",
}

TEN_GOD_FAMILY = {
    "比肩": "peer",
    "劫财": "peer",
    "食神": "output",
    "伤官": "output",
    "正财": "wealth",
    "偏财": "wealth",
    "正官": "official_killings",
    "七杀": "official_killings",
    "正印": "resource",
    "偏印": "resource",
}


def _element_family(day_master: str, other_element: str) -> str:
    dm_element = STEM_ELEMENT[day_master]
    if other_element == dm_element:
        return "peer"

    # Infer the broad ten-god family through a representative stem of the
    # transformed element. Polarity is deliberately discarded because a
    # branch transformation identifies an element family, not one exact stem.
    representative = next(stem for stem, element in STEM_ELEMENT.items() if element == other_element)
    return TEN_GOD_FAMILY[ten_god(day_master, representative)]


def _pattern_from_exact_ten_god(day_master: str, month_branch: str, tg: str) -> str:
    if month_branch == YANG_BLADE_BRANCH.get(day_master) and tg in {"比肩", "劫财"}:
        return "阳刃格"
    if tg == "正官":
        return "官格"
    if tg in {"正财", "偏财"}:
        return "财格"
    if tg in {"正印", "偏印"}:
        return "印格"
    if tg == "食神":
        return "食神格"
    if tg == "七杀":
        return "七杀格"
    if tg == "伤官":
        return "伤官格"
    return "建禄月劫"


def _full_harmony_element(month_branch: str, branches: list[str]) -> str | None:
    branch_set = set(branches)
    for group, element in THREE_HARMONY_ELEMENT.items():
        if month_branch in group and group.issubset(branch_set):
            return element
    return None


def month_use_features_from_pillars(year: str, month: str, day: str, time: str) -> dict[str, object]:
    """Operationalize 《子平真诠》 month-use change primitives without weights.

    This layer encodes only mechanically testable statements:
    - month-command hidden stems;
    - whether each hidden stem transmits to year/month/time stems;
    - primary-qi preference when it transmits;
    - secondary hidden stem taking the visible lead when primary qi does not;
    - complete three-harmony branch transformation involving the month branch;
    - single/combined use components.

    It deliberately does not assign a numeric fortune/strength score and does
    not claim that a branch-transformed element has one exact yin/yang ten god.
    """
    pillars = (year, month, day, time)
    if any(len(p) != 2 for p in pillars):
        raise ValueError("pillars must be two-character stem-branch strings")

    day_master = day[0]
    month_branch = month[1]
    month_hidden = HIDDEN_STEMS[month_branch]
    visible_stems = (year[0], month[0], time[0])
    branches = [year[1], month[1], day[1], time[1]]

    transmitted = tuple(stem for stem in month_hidden if stem in visible_stems)
    primary_stem = month_hidden[0]
    primary_tg = ten_god(day_master, primary_stem)
    primary_transmitted = primary_stem in transmitted
    secondary_transmitted = tuple(stem for stem in transmitted if stem != primary_stem)

    if primary_transmitted:
        selected_stem = primary_stem
        selection_mode = "primary_transmitted"
    elif secondary_transmitted:
        selected_stem = secondary_transmitted[0]
        selection_mode = "secondary_transmitted"
    else:
        selected_stem = primary_stem
        selection_mode = "primary_untransmitted_default"

    selected_tg = ten_god(day_master, selected_stem)
    selected_pattern = _pattern_from_exact_ten_god(day_master, month_branch, selected_tg)

    transformed_element = _full_harmony_element(month_branch, branches)
    transformed_family = _element_family(day_master, transformed_element) if transformed_element else ""
    primary_family = TEN_GOD_FAMILY[primary_tg]

    components: list[str] = [f"stem:{stem}:{ten_god(day_master, stem)}" for stem in transmitted]
    if transformed_element:
        components.append(f"branch_harmony:{transformed_element}:{transformed_family}")
    if not components:
        components.append(f"default_primary:{primary_stem}:{primary_tg}")

    exact_families = [TEN_GOD_FAMILY[ten_god(day_master, stem)] for stem in transmitted]
    all_families = exact_families + ([transformed_family] if transformed_family else [])
    if not all_families:
        all_families = [primary_family]

    unique_families = tuple(dict.fromkeys(all_families))
    main_changed_by_transmission = selected_stem != primary_stem
    main_changed_by_harmony = bool(transformed_family and transformed_family != primary_family)

    if transmitted and transformed_element:
        composition_mode = "transmission_plus_harmony"
    elif len(transmitted) >= 2:
        composition_mode = "multiple_transmitted"
    elif len(transmitted) == 1:
        composition_mode = "single_transmitted"
    elif transformed_element:
        composition_mode = "harmony_only"
    else:
        composition_mode = "default_primary_only"

    return {
        "zpzt_use__v2__month_branch": month_branch,
        "zpzt_use__v2__month_hidden_stems": "".join(month_hidden),
        "zpzt_use__v2__primary_stem": primary_stem,
        "zpzt_use__v2__primary_ten_god": primary_tg,
        "zpzt_use__v2__primary_family": primary_family,
        "zpzt_use__v2__primary_transmitted": int(primary_transmitted),
        "zpzt_use__v2__transmitted_stems": "".join(transmitted),
        "zpzt_use__v2__transmitted_count": len(transmitted),
        "zpzt_use__v2__secondary_transmitted_count": len(secondary_transmitted),
        "zpzt_use__v2__selected_stem": selected_stem,
        "zpzt_use__v2__selected_ten_god": selected_tg,
        "zpzt_use__v2__selected_pattern_candidate": selected_pattern,
        "zpzt_use__v2__selection_mode": selection_mode,
        "zpzt_use__v2__harmony_element": transformed_element or "",
        "zpzt_use__v2__harmony_family": transformed_family,
        "zpzt_use__v2__harmony_changes_family": int(main_changed_by_harmony),
        "zpzt_use__v2__transmission_changes_main": int(main_changed_by_transmission),
        "zpzt_use__v2__use_change_detected": int(main_changed_by_transmission or main_changed_by_harmony),
        "zpzt_use__v2__composition_mode": composition_mode,
        "zpzt_use__v2__component_count": len(components),
        "zpzt_use__v2__components": "|".join(components),
        "zpzt_use__v2__family_count": len(unique_families),
        "zpzt_use__v2__families": "|".join(unique_families),
        "zpzt_use__v2__mixed_families": int(len(unique_families) > 1),
        "zpzt_use__v2__aggregate_fortune_score_defined": 0,
    }


def add_ziping_use_v2_features(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "ganzhi__v2__year_pillar",
        "ganzhi__v2__month_pillar",
        "ganzhi__v2__day_pillar",
        "ganzhi__v2__time_pillar",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Ganzhi features required before Ziping use-v2 features: {missing}")

    rows = [
        month_use_features_from_pillars(y, m, d, t)
        for y, m, d, t in zip(*(df[c] for c in required))
    ]
    feat = pd.DataFrame(rows, index=df.index)
    return pd.concat([df.copy(), feat], axis=1)
