from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .bazi_ziping import HIDDEN_STEMS, OUTPUT, RESOURCE, WEALTH, ten_god
from .zpzt_use_v2 import TEN_GOD_FAMILY, month_use_features_from_pillars


STEM_COMBINATIONS = {
    frozenset(("甲", "己")),
    frozenset(("乙", "庚")),
    frozenset(("丙", "辛")),
    frozenset(("丁", "壬")),
    frozenset(("戊", "癸")),
}

VISIBLE_POSITIONS = (("year", 0), ("month", 1), ("time", 3))


@dataclass(frozen=True)
class Route:
    name: str
    status: str
    assistants: tuple[str, ...]
    reasons: tuple[str, ...]
    requires_strength: bool = False
    requires_position: bool = False
    requires_quantity: bool = False
    source_example: bool = False


def _visible_context(year: str, month: str, day: str, time: str) -> dict[str, object]:
    pillars = (year, month, day, time)
    dm = day[0]
    stems = [p[0] for p in pillars]
    branches = [p[1] for p in pillars]
    visible: list[dict[str, object]] = []
    for position, idx in VISIBLE_POSITIONS:
        stem = stems[idx]
        visible.append(
            {
                "position": position,
                "stem": stem,
                "ten_god": ten_god(dm, stem),
            }
        )

    all_hidden = {hs for branch in branches for hs in HIDDEN_STEMS[branch]}
    return {
        "dm": dm,
        "stems": stems,
        "branches": branches,
        "visible": visible,
        "visible_ten_gods": tuple(str(x["ten_god"]) for x in visible),
        "all_hidden": all_hidden,
    }


def _has(context: dict[str, object], labels: set[str] | frozenset[str]) -> bool:
    return bool(set(context["visible_ten_gods"]) & set(labels))


def _stems_for(context: dict[str, object], labels: set[str] | frozenset[str]) -> list[str]:
    return [
        str(x["stem"])
        for x in context["visible"]
        if str(x["ten_god"]) in labels
    ]


def _ten_gods_for(context: dict[str, object], labels: set[str] | frozenset[str]) -> list[str]:
    return [
        str(x["ten_god"])
        for x in context["visible"]
        if str(x["ten_god"]) in labels
    ]


def _has_combination_between(
    context: dict[str, object],
    left_labels: set[str] | frozenset[str],
    right_labels: set[str] | frozenset[str],
) -> bool:
    left = _stems_for(context, left_labels)
    right = _stems_for(context, right_labels)
    return any(frozenset((a, b)) in STEM_COMBINATIONS for a in left for b in right if a != b)


def _rooted(context: dict[str, object], labels: set[str] | frozenset[str]) -> bool:
    hidden = set(context["all_hidden"])
    return any(stem in hidden for stem in _stems_for(context, labels))


def _route(
    name: str,
    present: bool,
    *,
    assistants: tuple[str, ...] = (),
    reasons: tuple[str, ...] = (),
    requires_strength: bool = False,
    requires_position: bool = False,
    requires_quantity: bool = False,
    source_example: bool = False,
) -> Route:
    if not present:
        status = "absent"
    elif requires_strength or requires_position or requires_quantity:
        unresolved = []
        if requires_strength:
            unresolved.append("strength")
        if requires_position:
            unresolved.append("position")
        if requires_quantity:
            unresolved.append("quantity")
        status = "unresolved_" + "_and_".join(unresolved)
    else:
        status = "hit"
    return Route(
        name=name,
        status=status,
        assistants=assistants,
        reasons=reasons,
        requires_strength=requires_strength,
        requires_position=requires_position,
        requires_quantity=requires_quantity,
        source_example=source_example,
    )


def route_graph_from_pillars(year: str, month: str, day: str, time: str) -> dict[str, object]:
    """Build a non-numeric 相神 / 成格 / 救应 route graph.

    The graph encodes explicit route predicates from 《子平真诠》. It does not
    assign scores, does not resolve classical terms such as 身强/印轻/伤旺 with
    arbitrary weights, and marks those routes as unresolved conditions instead.
    """
    use = month_use_features_from_pillars(year, month, day, time)
    c = _visible_context(year, month, day, time)

    selected_tg = str(use["zpzt_use__v2__selected_ten_god"])
    base_pattern = str(use["zpzt_use__v2__selected_pattern_candidate"])
    harmony_family = str(use["zpzt_use__v2__harmony_family"])
    harmony_changes = bool(use["zpzt_use__v2__harmony_changes_family"])
    selected_family = TEN_GOD_FAMILY[selected_tg]
    effective_family = harmony_family if harmony_changes and harmony_family else selected_family
    effective_scope = "family_only_from_harmony" if harmony_changes and harmony_family else "exact_ten_god"

    has_wealth = _has(c, set(WEALTH))
    has_resource = _has(c, set(RESOURCE))
    has_output = _has(c, set(OUTPUT))
    has_official = _has(c, {"正官"})
    has_killing = _has(c, {"七杀"})
    has_food = _has(c, {"食神"})
    has_hurting = _has(c, {"伤官"})
    has_peer = _has(c, {"比肩", "劫财"})
    has_robwealth = _has(c, {"劫财"})
    has_indirect_resource = _has(c, {"偏印"})

    harmony_output = harmony_family == "output"
    harmony_wealth = harmony_family == "wealth"
    harmony_resource = harmony_family == "resource"
    harmony_official = harmony_family == "official_killings"
    route_has_output = has_output or harmony_output
    route_has_wealth = has_wealth or harmony_wealth
    route_has_resource = has_resource or harmony_resource
    route_has_official_killing = has_official or has_killing or harmony_official

    routes: list[Route] = []

    if base_pattern == "官格":
        routes.extend(
            [
                _route(
                    "official_wealth_generates_use",
                    has_wealth,
                    assistants=tuple(_ten_gods_for(c, set(WEALTH))),
                    reasons=("官逢财生：官为用，财为相",),
                ),
                _route(
                    "official_resource_protects_use",
                    has_resource,
                    assistants=tuple(_ten_gods_for(c, set(RESOURCE))),
                    reasons=("官喜生印以护官",),
                ),
                _route(
                    "official_resource_combines_hurting_rescue",
                    has_hurting
                    and has_resource
                    and _has_combination_between(c, set(RESOURCE), {"伤官"}),
                    assistants=tuple(_ten_gods_for(c, set(RESOURCE))),
                    reasons=("官见伤而印与伤合：合伤存官的机械候选",),
                    source_example=True,
                ),
            ]
        )

    elif base_pattern == "财格":
        routes.extend(
            [
                _route(
                    "wealth_official_protects_use",
                    has_official,
                    assistants=("正官",),
                    reasons=("财旺生官：财为用，官为相",),
                ),
                _route(
                    "wealth_food_generates_use",
                    has_food and has_peer,
                    assistants=tuple(_ten_gods_for(c, {"食神", "比肩", "劫财"})),
                    reasons=("财逢食生而身强带比；已见食与比，身强仍待判",),
                    requires_strength=True,
                ),
                _route(
                    "wealth_resource_position_route",
                    has_resource,
                    assistants=tuple(_ten_gods_for(c, set(RESOURCE))),
                    reasons=("财格透印而位置妥贴、两不相克；位置条件保留未决",),
                    requires_position=True,
                ),
                _route(
                    "wealth_robwealth_combines_killing_rescue",
                    has_killing
                    and has_robwealth
                    and _has_combination_between(c, {"劫财"}, {"七杀"}),
                    assistants=("劫财",),
                    reasons=("财用遇杀而劫与杀合：合杀存财的机械候选",),
                    source_example=True,
                ),
            ]
        )

    elif base_pattern == "印格":
        routes.extend(
            [
                _route(
                    "resource_official_generates_use",
                    has_official,
                    assistants=("正官",),
                    reasons=("官印双全：官生印",),
                ),
                _route(
                    "resource_killing_generates_use",
                    has_killing,
                    assistants=("七杀",),
                    reasons=("印轻逢杀；印轻为量级条件，保留未决",),
                    requires_quantity=True,
                ),
                _route(
                    "resource_output_releases_excess",
                    has_output,
                    assistants=tuple(_ten_gods_for(c, set(OUTPUT))),
                    reasons=("身印两旺而用食伤泄气；身印两旺保留未决",),
                    requires_strength=True,
                    requires_quantity=True,
                ),
                _route(
                    "resource_wealth_relieves_excess",
                    has_wealth,
                    assistants=tuple(_ten_gods_for(c, set(WEALTH))),
                    reasons=("印多逢财而财透根轻；印多与根轻保留未决",),
                    requires_quantity=True,
                ),
            ]
        )

    elif base_pattern == "食神格":
        routes.extend(
            [
                _route(
                    "food_wealth_receives_output",
                    has_wealth,
                    assistants=tuple(_ten_gods_for(c, set(WEALTH))),
                    reasons=("食神生财",),
                ),
                _route(
                    "food_abandons_to_killing_with_resource",
                    has_killing and has_resource and not has_wealth,
                    assistants=tuple(_ten_gods_for(c, {"七杀", "正印", "偏印"})),
                    reasons=("食带杀而无财，弃食就杀而透印",),
                ),
            ]
        )

    elif base_pattern == "七杀格":
        routes.extend(
            [
                _route(
                    "killing_food_controls_use",
                    has_food,
                    assistants=("食神",),
                    reasons=("杀逢食制；身强条件保留未决",),
                    requires_strength=True,
                ),
                _route(
                    "killing_food_released_by_combining_resource",
                    has_food
                    and has_indirect_resource
                    and has_wealth
                    and _has_combination_between(c, set(WEALTH), {"偏印"}),
                    assistants=tuple(_ten_gods_for(c, set(WEALTH))),
                    reasons=("食制杀受印阻，财与印合以使食得制杀的机械候选",),
                    requires_strength=True,
                    source_example=True,
                ),
            ]
        )

    elif base_pattern == "伤官格":
        routes.extend(
            [
                _route(
                    "hurting_wealth_transforms_use",
                    has_wealth,
                    assistants=tuple(_ten_gods_for(c, set(WEALTH))),
                    reasons=("伤官生财",),
                ),
                _route(
                    "hurting_resource_controls_use",
                    has_resource and _rooted(c, set(RESOURCE)),
                    assistants=tuple(_ten_gods_for(c, set(RESOURCE))),
                    reasons=("伤官佩印且印有根；伤官旺条件保留未决",),
                    requires_quantity=True,
                ),
                _route(
                    "hurting_killing_resource_route",
                    has_killing and has_resource,
                    assistants=tuple(_ten_gods_for(c, {"七杀", "正印", "偏印"})),
                    reasons=("伤官旺、身主弱而透杀印；旺弱条件保留未决",),
                    requires_strength=True,
                    requires_quantity=True,
                ),
                _route(
                    "hurting_killing_without_wealth",
                    has_killing and not has_wealth,
                    assistants=("七杀",),
                    reasons=("伤官带杀而无财",),
                ),
            ]
        )

    elif base_pattern == "阳刃格":
        routes.append(
            _route(
                "blade_official_killing_controls_use",
                route_has_official_killing and (route_has_wealth or route_has_resource) and not has_hurting,
                assistants=tuple(_ten_gods_for(c, {"正官", "七杀", "正财", "偏财", "正印", "偏印"})),
                reasons=("阳刃透官杀而露财印、不见伤官",),
            )
        )

    elif base_pattern == "建禄月劫":
        routes.extend(
            [
                _route(
                    "peer_official_with_wealth_or_resource",
                    has_official and (route_has_wealth or route_has_resource),
                    assistants=tuple(_ten_gods_for(c, {"正官", "正财", "偏财", "正印", "偏印"})),
                    reasons=("建禄月劫透官而逢财印",),
                ),
                _route(
                    "peer_wealth_with_output",
                    route_has_wealth and route_has_output,
                    assistants=tuple(_ten_gods_for(c, {"正财", "偏财", "食神", "伤官"})),
                    reasons=("建禄月劫透财而逢食伤",),
                ),
                _route(
                    "peer_killing_with_food_control",
                    has_killing and has_food,
                    assistants=("七杀", "食神"),
                    reasons=("建禄月劫透杀而遇制伏",),
                ),
                _route(
                    "peer_harmony_output_generates_wealth",
                    harmony_output and has_wealth,
                    assistants=tuple(_ten_gods_for(c, set(WEALTH))) + ("branch_harmony:output",),
                    reasons=("月劫遇财，支会输出之气以转劫生财的机械候选",),
                    source_example=True,
                ),
            ]
        )

    hit = [r for r in routes if r.status == "hit"]
    unresolved = [r for r in routes if r.status.startswith("unresolved_")]
    absent = [r for r in routes if r.status == "absent"]
    source_hits = [r for r in hit if r.source_example]

    assistant_labels = tuple(
        dict.fromkeys(label for route in hit + unresolved for label in route.assistants)
    )
    combination_pairs = 0
    visible = c["visible"]
    for i, left in enumerate(visible):
        for right in visible[i + 1 :]:
            if frozenset((str(left["stem"]), str(right["stem"]))) in STEM_COMBINATIONS:
                combination_pairs += 1

    route_state = (
        "route_hit"
        if hit
        else "route_unresolved"
        if unresolved
        else "no_registered_route_hit"
    )

    return {
        "zpzt_route__v3__base_pattern": base_pattern,
        "zpzt_route__v3__selected_use_ten_god": selected_tg,
        "zpzt_route__v3__selected_use_family": selected_family,
        "zpzt_route__v3__effective_use_family": effective_family,
        "zpzt_route__v3__effective_use_scope": effective_scope,
        "zpzt_route__v3__harmony_family": harmony_family,
        "zpzt_route__v3__route_state": route_state,
        "zpzt_route__v3__route_hit_count": len(hit),
        "zpzt_route__v3__route_unresolved_count": len(unresolved),
        "zpzt_route__v3__route_absent_count": len(absent),
        "zpzt_route__v3__route_hits": "|".join(r.name for r in hit),
        "zpzt_route__v3__route_unresolved": "|".join(r.name for r in unresolved),
        "zpzt_route__v3__assistant_count": len(assistant_labels),
        "zpzt_route__v3__assistants": "|".join(assistant_labels),
        "zpzt_route__v3__source_example_rescue_hit_count": len(source_hits),
        "zpzt_route__v3__source_example_rescue_hits": "|".join(r.name for r in source_hits),
        "zpzt_route__v3__requires_strength_route_count": sum(r.requires_strength for r in routes if r.status != "absent"),
        "zpzt_route__v3__requires_position_route_count": sum(r.requires_position for r in routes if r.status != "absent"),
        "zpzt_route__v3__requires_quantity_route_count": sum(r.requires_quantity for r in routes if r.status != "absent"),
        "zpzt_route__v3__visible_combination_pair_count": combination_pairs,
        "zpzt_route__v3__aggregate_score_defined": 0,
    }


def add_ziping_route_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "ganzhi__v2__year_pillar",
        "ganzhi__v2__month_pillar",
        "ganzhi__v2__day_pillar",
        "ganzhi__v2__time_pillar",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Ganzhi features required before Ziping route-v3 features: {missing}")

    rows = [
        route_graph_from_pillars(y, m, d, t)
        for y, m, d, t in zip(*(df[c] for c in required))
    ]
    feat = pd.DataFrame(rows, index=df.index)
    return pd.concat([df.copy(), feat], axis=1)
