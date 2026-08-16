from __future__ import annotations

import pandas as pd

from .bazi_ziping import add_ziping_features
from .calendar_cycle import add_calendar_cycle_features
from .calendar_features import add_gregorian_features
from .ganzhi import add_ganzhi_features
from .zpzt_route_v3 import add_ziping_route_v3_features
from .zpzt_route_v4 import add_ziping_route_v4_features
from .zpzt_state import add_ziping_state_features
from .zpzt_strength import add_ziping_strength_primitives
from .zpzt_structure_v4 import add_ziping_structure_v4_features
from .zpzt_use_v2 import add_ziping_use_v2_features


def add_ziping_symbolic_state(df: pd.DataFrame) -> pd.DataFrame:
    """Add the frozen Ziping feature stack without labels or market data."""
    if "date" not in df.columns:
        raise ValueError("Ziping symbolic state requires date")
    out = df.copy()
    if "symbol" not in out.columns:
        out["symbol"] = "MARKET"
    out = add_gregorian_features(out)
    out = add_ganzhi_features(out)
    out = add_ziping_features(out)
    out = add_ziping_use_v2_features(out)
    out = add_ziping_route_v3_features(out)
    out = add_ziping_structure_v4_features(out)
    out = add_ziping_route_v4_features(out)
    out = add_ziping_strength_primitives(out)
    out = add_ziping_state_features(out)
    return out


def premarket_symbolic_feature_row(target_date: str | pd.Timestamp) -> pd.DataFrame:
    """Create date-only deterministic Cycle + Ziping state for the target session."""
    target = pd.Timestamp(target_date).normalize()
    out = pd.DataFrame({"date": [target], "symbol": ["MARKET"]})
    out = add_ziping_symbolic_state(out)
    out = add_calendar_cycle_features(out)
    return out
