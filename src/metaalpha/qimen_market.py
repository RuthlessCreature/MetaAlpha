from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from .qimen_v1 import TZ_SHANGHAI, build_qimen_plate


MARKET_HOUR = 9
MARKET_MINUTE = 25


def _market_datetime(value) -> datetime:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize(TZ_SHANGHAI)
    else:
        ts = ts.tz_convert(TZ_SHANGHAI)
    ts = ts.replace(hour=MARKET_HOUR, minute=MARKET_MINUTE, second=0, microsecond=0)
    return ts.to_pydatetime()


def _star_label(plate: dict[str, object], palace: int) -> str:
    values = plate["heaven_stars"][palace]
    return "+".join(values) if values else ""


def _palace_composition(plate: dict[str, object], palace: int, *, include_door: bool = True) -> str:
    star = _star_label(plate, palace)
    door = plate["doors"].get(palace, "") if include_door else ""
    spirit = plate["spirits"].get(palace, "")
    return f"star={star}|door={door}|spirit={spirit}"


def qimen_market_features_for_date(value) -> dict[str, object]:
    dt = _market_datetime(value)
    plate = build_qimen_plate(dt)

    duty = plate["duty"]
    states = plate["states"]
    ju = plate["ju"]
    xun = plate["xun"]

    star_palace = int(duty["star_display_palace"])
    door_palace = int(duty["door_display_palace"])
    yima_palace = int(states["yima_palace"])
    day_void = set(states["day_xunkong_palaces"])
    hour_void = set(states["hour_xunkong_palaces"])

    if int(states["star_fuyin"]) == 1:
        star_state = "伏吟"
    elif int(states["star_fanyin"]) == 1:
        star_state = "反吟"
    else:
        star_state = "常态"

    void_bits = (
        int(star_palace in day_void),
        int(door_palace in day_void),
        int(star_palace in hour_void),
        int(door_palace in hour_void),
    )
    void_state = (
        f"day_star={void_bits[0]}|day_door={void_bits[1]}|"
        f"hour_star={void_bits[2]}|hour_door={void_bits[3]}"
    )

    yima_star = int(yima_palace == star_palace)
    yima_door = int(yima_palace == door_palace)
    yima_state = f"palace={yima_palace}|star={yima_star}|door={yima_door}"

    return {
        "qimen__v1__dun": ju["dun"],
        "qimen__v1__ju_number": int(ju["number"]),
        "qimen__v1__yuan": ju["yuan"],
        "qimen__v1__dun_ju_yuan": f"{ju['dun']}{ju['number']}|{ju['yuan']}",
        "qimen__v1__duty_star": duty["star"],
        "qimen__v1__duty_door": duty["door"],
        "qimen__v1__duty_star_door": f"{duty['star']}|{duty['door']}",
        "qimen__v1__duty_star_palace": star_palace,
        "qimen__v1__duty_door_palace": door_palace,
        "qimen__v1__duty_landings": f"star={star_palace}|door={door_palace}",
        "qimen__v1__star_steps": int(duty["star_steps"]),
        "qimen__v1__door_steps": int(duty["door_steps"]),
        "qimen__v1__star_state": star_state,
        "qimen__v1__rotation_state": f"star={duty['star_steps']}|door={duty['door_steps']}|{star_state}",
        "qimen__v1__xun_true_source_palace": int(xun["true_source_palace"]),
        "qimen__v1__hour_target_true_palace": int(duty["hour_target_true_palace"]),
        "qimen__v1__xun_target_state": (
            f"source={xun['true_source_palace']}|target={duty['hour_target_true_palace']}"
        ),
        "qimen__v1__day_void_hits_duty_star": void_bits[0],
        "qimen__v1__day_void_hits_duty_door": void_bits[1],
        "qimen__v1__hour_void_hits_duty_star": void_bits[2],
        "qimen__v1__hour_void_hits_duty_door": void_bits[3],
        "qimen__v1__void_relation_state": void_state,
        "qimen__v1__yima_palace": yima_palace,
        "qimen__v1__yima_hits_duty_star": yima_star,
        "qimen__v1__yima_hits_duty_door": yima_door,
        "qimen__v1__yima_relation_state": yima_state,
        "qimen__v1__door_at_duty_star_palace": plate["doors"].get(star_palace, ""),
        "qimen__v1__star_at_duty_door_palace": _star_label(plate, door_palace),
        "qimen__v1__spirit_at_duty_door_palace": plate["spirits"].get(door_palace, ""),
        "qimen__v1__duty_door_palace_composition": _palace_composition(plate, door_palace),
        "qimen__v1__yima_palace_composition": _palace_composition(plate, yima_palace),
        "qimen__v1__solar_term": plate["solar_term"]["name"],
        "qimen__v1__day_pillar": plate["pillars"]["day"],
        "qimen__v1__hour_pillar": plate["pillars"]["time"],
        "qimen__v1__engine_id": plate["engine_id"],
        "qimen__v1__aggregate_score_defined": 0,
    }


def add_qimen_market_features(df: pd.DataFrame, *, date_col: str = "date") -> pd.DataFrame:
    out = df.copy()
    rows = [qimen_market_features_for_date(value) for value in out[date_col]]
    feat = pd.DataFrame(rows, index=out.index)
    return pd.concat([out, feat], axis=1)
