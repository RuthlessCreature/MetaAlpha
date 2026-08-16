from __future__ import annotations

import pandas as pd

from .calendar_cycle import add_calendar_cycle_features
from .liuyao_hash import add_liuyao_hash_features
from .market_baseline import (
    BASE_CATEGORICAL,
    BASE_CONTINUOUS,
    TARGET_DIRECTION,
    TARGET_RETURN,
    add_market_baseline_features,
    premarket_market_feature_row,
)
from .meihua import add_meihua_features
from .pipeline import build_dataset
from .qimen_market import add_qimen_market_features
from .symbolic_state import premarket_symbolic_feature_row


META_CANDIDATE_FEATURES: dict[str, list[str]] = {
    "cycle": [
        "cycle__v1__prev_jieqi",
        "cycle__v1__jieqi_phase_quartile",
        "cycle__v1__day_pillar",
        "cycle__v1__month_stem",
        "cycle__v1__month_branch",
    ],
    "ziping": [
        "zpzt_use__v2__selected_ten_god",
        "zpzt_use__v2__selection_mode",
        "zpzt_route__v3__route_state",
        "zpzt_structure__v4__wealth_resource_position_resolution",
        "zpzt_structure__v4__selected_use_root_bin",
        "zpzt_structure__v4__support_profile",
    ],
    "qimen": [
        "qimen__v1__dun_ju_yuan",
        "qimen__v1__duty_star_door",
        "qimen__v1__duty_landings",
        "qimen__v1__rotation_state",
        "qimen__v1__void_relation_state",
        "qimen__v1__yima_relation_state",
    ],
    "meihua": [
        "meihua__v1__base_hexagram_key",
        "meihua__v1__moving_line",
        "meihua__v1__changed_hexagram_key",
        "meihua__v1__mutual_hexagram_key",
        "meihua__v1__body_use_relation",
    ],
}

META_NEGATIVE_CONTROL_FEATURES: dict[str, list[str]] = {
    "liuyao_hash": [
        "liuyao_hash__v1__base_pattern",
        "liuyao_hash__v1__changed_pattern",
        "liuyao_hash__v1__moving_count",
        "liuyao_hash__v1__moving_lines_key",
    ]
}

META_ALL_MODELS = tuple(META_CANDIDATE_FEATURES) + tuple(META_NEGATIVE_CONTROL_FEATURES)


def build_meta_historical_dataset(raw: pd.DataFrame) -> pd.DataFrame:
    """Build the common frozen META_FWD_001 training frame."""
    out = add_market_baseline_features(raw)
    out = build_dataset(out, include_ziping=True, include_natal_transit=False)
    out = add_calendar_cycle_features(out)
    out = add_qimen_market_features(out)
    out = add_meihua_features(out)
    out = add_liuyao_hash_features(out)

    symbolic = []
    for cols in META_CANDIDATE_FEATURES.values():
        symbolic.extend(cols)
    for cols in META_NEGATIVE_CONTROL_FEATURES.values():
        symbolic.extend(cols)
    symbolic = list(dict.fromkeys(symbolic))
    required = [
        "date",
        TARGET_DIRECTION,
        TARGET_RETURN,
        *BASE_CONTINUOUS,
        *BASE_CATEGORICAL,
        *symbolic,
    ]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"META_FWD_001 dataset missing registered columns: {missing}")
    out = out.dropna(subset=required).copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.normalize()
    out[TARGET_DIRECTION] = out[TARGET_DIRECTION].astype(int)
    return out.sort_values("date").reset_index(drop=True)


def premarket_meta_feature_row(history: pd.DataFrame, target_date) -> pd.DataFrame:
    market = premarket_market_feature_row(history, target_date)
    symbolic = premarket_symbolic_feature_row(target_date)
    symbolic = add_qimen_market_features(symbolic)
    symbolic = add_meihua_features(symbolic)
    symbolic = add_liuyao_hash_features(symbolic)
    out = market.merge(symbolic, on="date", how="inner", validate="one_to_one")

    required = list(BASE_CONTINUOUS) + list(BASE_CATEGORICAL)
    for cols in META_CANDIDATE_FEATURES.values():
        required.extend(cols)
    for cols in META_NEGATIVE_CONTROL_FEATURES.values():
        required.extend(cols)
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"premarket META_FWD_001 row missing registered columns: {missing}")
    return out
