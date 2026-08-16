from __future__ import annotations

import pandas as pd

from .zpzt_route_v3 import route_graph_from_pillars
from .zpzt_structure_v4 import structure_features_from_pillars


def _split_routes(value: object) -> list[str]:
    return [x for x in str(value).split("|") if x]


def refined_route_features_from_pillars(year: str, month: str, day: str, time: str) -> dict[str, object]:
    """Refine only classical route predicates that v4 can resolve mechanically.

    At present this resolves the 财格佩印 position predicate using a frozen
    source-based rule:

    - visible wealth/resource pairs only separated by >=2 stem positions -> satisfied;
    - only directly adjacent pairs -> blocked;
    - both adjacent and separated pairs -> ambiguous;
    - if both visible families are not present -> the v3 position dependency
      remains unresolved.

    No strength/quantity condition is resolved here.
    """
    v3 = route_graph_from_pillars(year, month, day, time)
    structure = structure_features_from_pillars(year, month, day, time)

    original_hits = _split_routes(v3["zpzt_route__v3__route_hits"])
    original_unresolved = _split_routes(v3["zpzt_route__v3__route_unresolved"])
    refined_hits = list(original_hits)
    still_unresolved = list(original_unresolved)
    blocked: list[str] = []
    resolved_from_position: list[str] = []

    target = "wealth_resource_position_route"
    position_resolution = str(structure["zpzt_structure__v4__wealth_resource_position_resolution"])
    if target in still_unresolved:
        if position_resolution == "position_condition_satisfied":
            still_unresolved.remove(target)
            refined_hits.append(target)
            resolved_from_position.append(target)
        elif position_resolution == "position_condition_blocked":
            still_unresolved.remove(target)
            blocked.append(target)
        elif position_resolution == "position_condition_ambiguous_multiple":
            pass
        else:
            # There is not enough visible position evidence to resolve the v3
            # dependency, so it remains explicitly unresolved.
            pass

    if refined_hits:
        state = "route_hit"
    elif still_unresolved:
        state = "route_unresolved"
    elif blocked:
        state = "route_blocked"
    else:
        state = "no_registered_route_hit"

    return {
        "zpzt_route__v4__route_state": state,
        "zpzt_route__v4__route_hit_count": len(refined_hits),
        "zpzt_route__v4__route_unresolved_count": len(still_unresolved),
        "zpzt_route__v4__route_blocked_count": len(blocked),
        "zpzt_route__v4__route_hits": "|".join(refined_hits),
        "zpzt_route__v4__route_unresolved": "|".join(still_unresolved),
        "zpzt_route__v4__route_blocked": "|".join(blocked),
        "zpzt_route__v4__resolved_from_position_count": len(resolved_from_position),
        "zpzt_route__v4__resolved_from_position": "|".join(resolved_from_position),
        "zpzt_route__v4__wealth_resource_position_resolution": position_resolution,
        "zpzt_route__v4__strength_resolution_applied": 0,
        "zpzt_route__v4__quantity_resolution_applied": 0,
        "zpzt_route__v4__aggregate_score_defined": 0,
    }


def add_ziping_route_v4_features(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "ganzhi__v2__year_pillar",
        "ganzhi__v2__month_pillar",
        "ganzhi__v2__day_pillar",
        "ganzhi__v2__time_pillar",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Ganzhi features required before Ziping route-v4 features: {missing}")

    rows = [
        refined_route_features_from_pillars(y, m, d, t)
        for y, m, d, t in zip(*(df[c] for c in required))
    ]
    feat = pd.DataFrame(rows, index=df.index)
    return pd.concat([df.copy(), feat], axis=1)
