from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

import pandas as pd

from .bazi_ziping import BREAKS, CLASHES, HARMS, HIDDEN_STEMS, features_from_pillars, ten_god
from .ganzhi import Pillars, pillars_from_datetime

TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")

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


@dataclass(frozen=True)
class NatalChartSpec:
    id: str
    anchor: datetime
    source: str
    rationale: str


SSE_NATAL_V1 = NatalChartSpec(
    id="SSE_NATAL_V1",
    anchor=datetime(1990, 12, 19, 11, 0, tzinfo=TZ_SHANGHAI),
    source="Shanghai Stock Exchange / China Securities Museum: opening gong at 11:00 on 1990-12-19",
    rationale="Exact independently sourced market-opening event; frozen before natal-transit testing.",
)


def _has_pair(relation: set[frozenset[str]], a: str, b: str) -> bool:
    return frozenset((a, b)) in relation


def _pillars_as_lists(p: Pillars) -> tuple[list[str], list[str]]:
    ps = (p.year, p.month, p.day, p.time)
    return [x[0] for x in ps], [x[1] for x in ps]


@lru_cache(maxsize=32)
def natal_pillars(spec: NatalChartSpec = SSE_NATAL_V1) -> Pillars:
    """Calculate an immutable natal chart once per frozen chart specification."""
    return pillars_from_datetime(spec.anchor)


@lru_cache(maxsize=32)
def _natal_static_items(spec: NatalChartSpec = SSE_NATAL_V1) -> tuple[tuple[str, object], ...]:
    p = natal_pillars(spec)
    z = features_from_pillars(p.year, p.month, p.day, p.time)
    return tuple(
        {
            "natal__v1__chart_id": spec.id,
            "natal__v1__anchor": spec.anchor.isoformat(),
            "natal__v1__year_pillar": p.year,
            "natal__v1__month_pillar": p.month,
            "natal__v1__day_pillar": p.day,
            "natal__v1__time_pillar": p.time,
            "natal__v1__day_master": p.day_stem,
            "natal__v1__pattern_candidate": z["zpzt__v1__pattern_candidate"],
            "natal__v1__month_primary_ten_god": z["zpzt__v1__month_primary_ten_god"],
            "natal__v1__use_mode": z["zpzt__v1__use_mode"],
        }.items()
    )


def natal_static_features(spec: NatalChartSpec = SSE_NATAL_V1) -> dict[str, object]:
    # Return a fresh dict so callers cannot mutate the cached representation.
    return dict(_natal_static_items(spec))


def features_for_transit_datetime(
    value,
    *,
    spec: NatalChartSpec = SSE_NATAL_V1,
    transit_anchor_hour: int = 9,
    transit_anchor_minute: int = 25,
) -> dict[str, object]:
    """Encode raw natal-chart × transit relations without a fortune score."""
    natal = natal_pillars(spec)
    transit = pillars_from_datetime(value, transit_anchor_hour, transit_anchor_minute)
    natal_stems, natal_branches = _pillars_as_lists(natal)
    transit_stems, transit_branches = _pillars_as_lists(transit)
    dm = natal.day_stem

    out = natal_static_features(spec)
    labels = ("year", "month", "day", "time")

    total_clash = 0
    total_harm = 0
    total_break = 0
    total_six_combine = 0
    total_stem_combine = 0

    for label, stem, branch in zip(labels, transit_stems, transit_branches):
        prefix = f"natal_transit__v1__{label}"
        primary_hidden = HIDDEN_STEMS[branch][0]
        out[f"{prefix}_pillar"] = stem + branch
        out[f"{prefix}_stem_ten_god"] = ten_god(dm, stem)
        out[f"{prefix}_branch_primary_ten_god"] = ten_god(dm, primary_hidden)

        stem_combines = sum(_has_pair(STEM_COMBINATIONS, stem, n) for n in natal_stems)
        clashes = sum(_has_pair(CLASHES, branch, n) for n in natal_branches)
        harms = sum(_has_pair(HARMS, branch, n) for n in natal_branches)
        breaks = sum(_has_pair(BREAKS, branch, n) for n in natal_branches)
        combines = sum(_has_pair(BRANCH_SIX_COMBINATIONS, branch, n) for n in natal_branches)

        out[f"{prefix}_stem_combines_natal_count"] = int(stem_combines)
        out[f"{prefix}_branch_clashes_natal_count"] = int(clashes)
        out[f"{prefix}_branch_harms_natal_count"] = int(harms)
        out[f"{prefix}_branch_breaks_natal_count"] = int(breaks)
        out[f"{prefix}_branch_six_combines_natal_count"] = int(combines)

        total_stem_combine += stem_combines
        total_clash += clashes
        total_harm += harms
        total_break += breaks
        total_six_combine += combines

    td = transit.day_branch
    out["natal_transit__v1__day_clashes_natal_day"] = int(_has_pair(CLASHES, td, natal.day_branch))
    out["natal_transit__v1__day_clashes_natal_month"] = int(_has_pair(CLASHES, td, natal.month_branch))
    out["natal_transit__v1__day_harms_natal_day"] = int(_has_pair(HARMS, td, natal.day_branch))
    out["natal_transit__v1__day_harms_natal_month"] = int(_has_pair(HARMS, td, natal.month_branch))
    out["natal_transit__v1__day_breaks_natal_day"] = int(_has_pair(BREAKS, td, natal.day_branch))
    out["natal_transit__v1__day_breaks_natal_month"] = int(_has_pair(BREAKS, td, natal.month_branch))
    out["natal_transit__v1__day_six_combines_natal_day"] = int(_has_pair(BRANCH_SIX_COMBINATIONS, td, natal.day_branch))
    out["natal_transit__v1__day_six_combines_natal_month"] = int(_has_pair(BRANCH_SIX_COMBINATIONS, td, natal.month_branch))

    out["natal_transit__v1__stem_combine_count"] = int(total_stem_combine)
    out["natal_transit__v1__branch_clash_count"] = int(total_clash)
    out["natal_transit__v1__branch_harm_count"] = int(total_harm)
    out["natal_transit__v1__branch_break_count"] = int(total_break)
    out["natal_transit__v1__branch_six_combine_count"] = int(total_six_combine)
    out["natal_transit__v1__disruption_relation_count"] = int(total_clash + total_harm + total_break)

    # Explicitly refuse a hand-tuned good/bad aggregate. These are primitives.
    out["natal_transit__v1__fortune_score_defined"] = 0
    return out


def add_sse_natal_transit_features(
    df: pd.DataFrame,
    *,
    date_col: str = "date",
    spec: NatalChartSpec = SSE_NATAL_V1,
) -> pd.DataFrame:
    out = df.copy()
    rows = [features_for_transit_datetime(v, spec=spec) for v in out[date_col]]
    feat = pd.DataFrame(rows, index=out.index)
    return pd.concat([out, feat], axis=1)
