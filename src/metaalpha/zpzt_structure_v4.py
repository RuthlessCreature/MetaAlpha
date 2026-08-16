from __future__ import annotations

from collections import Counter

import pandas as pd

from .bazi_ziping import HIDDEN_STEMS, ten_god
from .zpzt_route_v3 import route_graph_from_pillars
from .zpzt_use_v2 import TEN_GOD_FAMILY, month_use_features_from_pillars


STEM_POSITIONS = {"year": 0, "month": 1, "day": 2, "time": 3}
VISIBLE_HELPER_POSITIONS = (("year", 0), ("month", 1), ("time", 3))


def _root_flags(stem: str, branches: list[str]) -> tuple[int, tuple[int, ...]]:
    flags = tuple(int(stem in HIDDEN_STEMS[branch]) for branch in branches)
    return sum(flags), flags


def _visible_helpers(year: str, month: str, day: str, time: str) -> list[dict[str, object]]:
    pillars = (year, month, day, time)
    dm = day[0]
    branches = [p[1] for p in pillars]
    rows: list[dict[str, object]] = []
    for position, idx in VISIBLE_HELPER_POSITIONS:
        stem = pillars[idx][0]
        tg = ten_god(dm, stem)
        root_count, root_flags = _root_flags(stem, branches)
        rows.append(
            {
                "position": position,
                "position_index": STEM_POSITIONS[position],
                "stem": stem,
                "ten_god": tg,
                "family": TEN_GOD_FAMILY[tg],
                "root_count": root_count,
                "root_year": root_flags[0],
                "root_month": root_flags[1],
                "root_day": root_flags[2],
                "root_time": root_flags[3],
            }
        )
    return rows


def _pair_position_state(
    helpers: list[dict[str, object]],
    left_family: str,
    right_family: str,
) -> tuple[str, list[int]]:
    left = [int(x["position_index"]) for x in helpers if x["family"] == left_family]
    right = [int(x["position_index"]) for x in helpers if x["family"] == right_family]
    if not left or not right:
        return "absent", []
    distances = sorted(abs(a - b) for a in left for b in right if a != b)
    if not distances:
        return "absent", []
    adjacent = any(d == 1 for d in distances)
    separated = any(d >= 2 for d in distances)
    if adjacent and separated:
        return "mixed_adjacent_and_separated", distances
    if adjacent:
        return "adjacent_only", distances
    return "separated_only", distances


def _root_bin(count: int) -> str:
    return "0" if count == 0 else "1" if count == 1 else "2plus"


def _balance_label(support: int, drain: int) -> str:
    if support > drain:
        return "support_gt_drain"
    if support < drain:
        return "drain_gt_support"
    return "support_eq_drain"


def structure_features_from_pillars(year: str, month: str, day: str, time: str) -> dict[str, object]:
    """Raw position/root/support primitives for unresolved classical conditions.

    V4 intentionally distinguishes *evidence* from *judgment*. It can resolve a
    narrow source-defined positional predicate (财印相邻 vs 隔离), but it does not
    convert rooting/support counts into a fitted or hand-weighted strong/weak
    score.
    """
    pillars = (year, month, day, time)
    if any(len(p) != 2 for p in pillars):
        raise ValueError("pillars must be two-character stem-branch strings")

    dm = day[0]
    branches = [p[1] for p in pillars]
    helpers = _visible_helpers(year, month, day, time)
    use = month_use_features_from_pillars(year, month, day, time)
    route = route_graph_from_pillars(year, month, day, time)

    family_visible_counts = Counter(str(x["family"]) for x in helpers)
    family_rooted_visible_counts = Counter(
        str(x["family"]) for x in helpers if int(x["root_count"]) > 0
    )
    tg_visible_counts = Counter(str(x["ten_god"]) for x in helpers)

    selected_stem = str(use["zpzt_use__v2__selected_stem"])
    selected_tg = str(use["zpzt_use__v2__selected_ten_god"])
    selected_root_count, selected_root_flags = _root_flags(selected_stem, branches)
    selected_visible_positions = [
        int(x["position_index"]) for x in helpers if x["stem"] == selected_stem
    ]

    wealth_resource_state, wealth_resource_distances = _pair_position_state(
        helpers, "wealth", "resource"
    )
    wealth_positions = sorted(
        int(x["position_index"]) for x in helpers if x["family"] == "wealth"
    )
    resource_positions = sorted(
        int(x["position_index"]) for x in helpers if x["family"] == "resource"
    )

    support_tgs = {"比肩", "劫财", "正印", "偏印"}
    drain_tgs = {"食神", "伤官", "正财", "偏财", "正官", "七杀"}
    visible_support = sum(tg_visible_counts[x] for x in support_tgs)
    visible_drain = sum(tg_visible_counts[x] for x in drain_tgs)
    dm_root_count, dm_root_flags = _root_flags(dm, branches)

    month_support = int(ten_god(dm, month[0]) in support_tgs)
    # The month *stem* relation is kept separately from the existing month-branch
    # element primitive. V4 combines neither into a scalar.
    support_profile = (
        f"monthstem_{'support' if month_support else 'nonsupport'}"
        f"|dmroot_{_root_bin(dm_root_count)}"
        f"|visible_{_balance_label(visible_support, visible_drain)}"
    )

    assistant_labels = [x for x in str(route["zpzt_route__v3__assistants"]).split("|") if x]
    assistant_ten_gods = {x for x in assistant_labels if x in TEN_GOD_FAMILY}
    assistant_helpers = [x for x in helpers if x["ten_god"] in assistant_ten_gods]
    assistant_rooted = [x for x in assistant_helpers if int(x["root_count"]) > 0]

    if wealth_resource_state == "separated_only":
        wealth_resource_resolution = "position_condition_satisfied"
    elif wealth_resource_state == "adjacent_only":
        wealth_resource_resolution = "position_condition_blocked"
    elif wealth_resource_state == "mixed_adjacent_and_separated":
        wealth_resource_resolution = "position_condition_ambiguous_multiple"
    else:
        wealth_resource_resolution = "not_applicable"

    return {
        "zpzt_structure__v4__selected_use_ten_god": selected_tg,
        "zpzt_structure__v4__selected_use_root_count": int(selected_root_count),
        "zpzt_structure__v4__selected_use_root_bin": _root_bin(selected_root_count),
        "zpzt_structure__v4__selected_use_root_year": int(selected_root_flags[0]),
        "zpzt_structure__v4__selected_use_root_month": int(selected_root_flags[1]),
        "zpzt_structure__v4__selected_use_root_day": int(selected_root_flags[2]),
        "zpzt_structure__v4__selected_use_root_time": int(selected_root_flags[3]),
        "zpzt_structure__v4__selected_use_visible_count": len(selected_visible_positions),
        "zpzt_structure__v4__selected_use_visible_positions": "|".join(map(str, selected_visible_positions)),
        "zpzt_structure__v4__wealth_visible_count": int(family_visible_counts["wealth"]),
        "zpzt_structure__v4__resource_visible_count": int(family_visible_counts["resource"]),
        "zpzt_structure__v4__output_visible_count": int(family_visible_counts["output"]),
        "zpzt_structure__v4__official_killings_visible_count": int(family_visible_counts["official_killings"]),
        "zpzt_structure__v4__peer_visible_count": int(family_visible_counts["peer"]),
        "zpzt_structure__v4__wealth_rooted_visible_count": int(family_rooted_visible_counts["wealth"]),
        "zpzt_structure__v4__resource_rooted_visible_count": int(family_rooted_visible_counts["resource"]),
        "zpzt_structure__v4__output_rooted_visible_count": int(family_rooted_visible_counts["output"]),
        "zpzt_structure__v4__official_killings_rooted_visible_count": int(family_rooted_visible_counts["official_killings"]),
        "zpzt_structure__v4__peer_rooted_visible_count": int(family_rooted_visible_counts["peer"]),
        "zpzt_structure__v4__wealth_positions": "|".join(map(str, wealth_positions)),
        "zpzt_structure__v4__resource_positions": "|".join(map(str, resource_positions)),
        "zpzt_structure__v4__wealth_resource_position_state": wealth_resource_state,
        "zpzt_structure__v4__wealth_resource_min_distance": min(wealth_resource_distances) if wealth_resource_distances else -1,
        "zpzt_structure__v4__wealth_resource_max_distance": max(wealth_resource_distances) if wealth_resource_distances else -1,
        "zpzt_structure__v4__wealth_resource_position_resolution": wealth_resource_resolution,
        "zpzt_structure__v4__daymaster_exact_root_count": int(dm_root_count),
        "zpzt_structure__v4__daymaster_root_bin": _root_bin(dm_root_count),
        "zpzt_structure__v4__daymaster_root_month": int(dm_root_flags[1]),
        "zpzt_structure__v4__visible_support_count": int(visible_support),
        "zpzt_structure__v4__visible_drain_count": int(visible_drain),
        "zpzt_structure__v4__visible_support_balance": _balance_label(visible_support, visible_drain),
        "zpzt_structure__v4__support_profile": support_profile,
        "zpzt_structure__v4__assistant_ten_god_count": len(assistant_ten_gods),
        "zpzt_structure__v4__assistant_visible_stem_count": len(assistant_helpers),
        "zpzt_structure__v4__assistant_rooted_stem_count": len(assistant_rooted),
        "zpzt_structure__v4__assistant_all_visible_rooted": int(bool(assistant_helpers) and len(assistant_helpers) == len(assistant_rooted)),
        "zpzt_structure__v4__aggregate_strength_score_defined": 0,
        "zpzt_structure__v4__aggregate_fortune_score_defined": 0,
    }


def add_ziping_structure_v4_features(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "ganzhi__v2__year_pillar",
        "ganzhi__v2__month_pillar",
        "ganzhi__v2__day_pillar",
        "ganzhi__v2__time_pillar",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Ganzhi features required before Ziping structure-v4 features: {missing}")

    rows = [
        structure_features_from_pillars(y, m, d, t)
        for y, m, d, t in zip(*(df[c] for c in required))
    ]
    feat = pd.DataFrame(rows, index=df.index)
    return pd.concat([df.copy(), feat], axis=1)
