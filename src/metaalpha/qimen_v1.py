from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from lunar_python import Solar

from .calendar_cycle import JIE_QI_ALIASES
from .ganzhi import JIAZI, JIAZI_INDEX, Pillars, pillars_from_datetime


TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")
CENTER_HOST = 2
RING = (1, 8, 3, 4, 9, 2, 7, 6)

PALACE_META = {
    1: ("坎", "北"),
    2: ("坤", "西南"),
    3: ("震", "东"),
    4: ("巽", "东南"),
    5: ("中", "中"),
    6: ("乾", "西北"),
    7: ("兑", "西"),
    8: ("艮", "东北"),
    9: ("离", "南"),
}

SANQI_LIUYI = tuple("戊己庚辛壬癸丁丙乙")

STAR_HOME = {
    "天蓬": 1,
    "天芮": 2,
    "天冲": 3,
    "天辅": 4,
    "天禽": 5,
    "天心": 6,
    "天柱": 7,
    "天任": 8,
    "天英": 9,
}
PERIMETER_STARS = ("天蓬", "天芮", "天冲", "天辅", "天英", "天柱", "天任", "天心")

DOOR_HOME = {
    "休门": 1,
    "死门": 2,
    "伤门": 3,
    "杜门": 4,
    "开门": 6,
    "惊门": 7,
    "生门": 8,
    "景门": 9,
}

SPIRIT_ORDER = ("值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天")

XUN_HIDDEN = {
    0: "戊",   # 甲子旬
    10: "己",  # 甲戌旬
    20: "庚",  # 甲申旬
    30: "辛",  # 甲午旬
    40: "壬",  # 甲辰旬
    50: "癸",  # 甲寅旬
}
XUN_VOID = {
    0: ("戌", "亥"),
    10: ("申", "酉"),
    20: ("午", "未"),
    30: ("辰", "巳"),
    40: ("寅", "卯"),
    50: ("子", "丑"),
}

BRANCH_PALACE = {
    "子": 1,
    "丑": 8,
    "寅": 8,
    "卯": 3,
    "辰": 4,
    "巳": 4,
    "午": 9,
    "未": 2,
    "申": 2,
    "酉": 7,
    "戌": 6,
    "亥": 6,
}

YIMA_BRANCH = {
    "申": "寅", "子": "寅", "辰": "寅",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥",
    "亥": "巳", "卯": "巳", "未": "巳",
}

JU_TABLE = {
    "冬至": ("阳", (1, 7, 4)),
    "小寒": ("阳", (2, 8, 5)),
    "大寒": ("阳", (3, 9, 6)),
    "立春": ("阳", (8, 5, 2)),
    "雨水": ("阳", (9, 6, 3)),
    "惊蛰": ("阳", (1, 7, 4)),
    "春分": ("阳", (3, 9, 6)),
    "清明": ("阳", (4, 1, 7)),
    "谷雨": ("阳", (5, 2, 8)),
    "立夏": ("阳", (4, 1, 7)),
    "小满": ("阳", (5, 2, 8)),
    "芒种": ("阳", (6, 3, 9)),
    "夏至": ("阴", (9, 3, 6)),
    "小暑": ("阴", (8, 2, 5)),
    "大暑": ("阴", (7, 1, 4)),
    "立秋": ("阴", (2, 5, 8)),
    "处暑": ("阴", (1, 4, 7)),
    "白露": ("阴", (9, 3, 6)),
    "秋分": ("阴", (7, 1, 4)),
    "寒露": ("阴", (6, 9, 3)),
    "霜降": ("阴", (5, 8, 2)),
    "立冬": ("阴", (6, 9, 3)),
    "小雪": ("阴", (5, 8, 2)),
    "大雪": ("阴", (4, 7, 1)),
}
YUAN_NAMES = ("上元", "中元", "下元")


@dataclass(frozen=True)
class SolarTermState:
    name: str
    timestamp: datetime


@dataclass(frozen=True)
class JuState:
    dun: str
    ju: int
    yuan_index: int
    yuan: str
    day_index: int
    fu_head_index: int
    fu_head: str


@dataclass(frozen=True)
class XunState:
    xunshou: str
    hidden_instrument: str
    hour_index: int
    xun_start_index: int
    hour_offset: int


def _as_shanghai_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TZ_SHANGHAI)
    return dt.astimezone(TZ_SHANGHAI)


def _solar_datetime(solar) -> datetime:
    return datetime(
        solar.getYear(),
        solar.getMonth(),
        solar.getDay(),
        solar.getHour(),
        solar.getMinute(),
        solar.getSecond(),
        tzinfo=TZ_SHANGHAI,
    )


def current_solar_term(value: datetime | str) -> SolarTermState:
    """Return the exact previous/current solar term at timestamp precision."""
    dt = _as_shanghai_datetime(value)
    lunar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second).getLunar()
    jieqi = lunar.getPrevJieQi(False)
    if jieqi is None:
        raise ValueError(f"no previous solar term for {dt.isoformat()}")
    raw_name = jieqi.getName()
    name = JIE_QI_ALIASES.get(raw_name, raw_name)
    if name not in JU_TABLE:
        raise ValueError(f"solar term not registered in QIMEN_V1 72-ju table: {raw_name!r}")
    term_dt = _solar_datetime(jieqi.getSolar())
    if term_dt > dt:
        raise AssertionError(f"calendar engine returned future solar term {term_dt} for {dt}")
    return SolarTermState(name=name, timestamp=term_dt)


def determine_ju(day_pillar: str, jieqi: str) -> JuState:
    if day_pillar not in JIAZI_INDEX:
        raise ValueError(f"invalid day pillar: {day_pillar}")
    if jieqi not in JU_TABLE:
        raise ValueError(f"unsupported solar term: {jieqi}")
    day_index = JIAZI_INDEX[day_pillar]
    five_day_block = day_index // 5
    yuan_index = five_day_block % 3
    fu_head_index = five_day_block * 5
    dun, ju_values = JU_TABLE[jieqi]
    return JuState(
        dun=dun,
        ju=int(ju_values[yuan_index]),
        yuan_index=yuan_index,
        yuan=YUAN_NAMES[yuan_index],
        day_index=day_index,
        fu_head_index=fu_head_index,
        fu_head=JIAZI[fu_head_index],
    )


def determine_xun(hour_pillar: str) -> XunState:
    if hour_pillar not in JIAZI_INDEX:
        raise ValueError(f"invalid hour pillar: {hour_pillar}")
    hour_index = JIAZI_INDEX[hour_pillar]
    xun_start = (hour_index // 10) * 10
    return XunState(
        xunshou=JIAZI[xun_start],
        hidden_instrument=XUN_HIDDEN[xun_start],
        hour_index=hour_index,
        xun_start_index=xun_start,
        hour_offset=hour_index - xun_start,
    )


def _numeric_palace(start: int, offset: int, direction: int) -> int:
    if start not in range(1, 10):
        raise ValueError("palace must be 1..9")
    return ((start - 1 + direction * offset) % 9) + 1


def build_earth_plate(dun: str, ju: int) -> dict[int, str]:
    if dun not in {"阳", "阴"}:
        raise ValueError("dun must be 阳 or 阴")
    if ju not in range(1, 10):
        raise ValueError("ju must be 1..9")
    direction = 1 if dun == "阳" else -1
    plate: dict[int, str] = {}
    for i, stem in enumerate(SANQI_LIUYI):
        plate[_numeric_palace(ju, i, direction)] = stem
    return dict(sorted(plate.items()))


def _palace_of_stem(earth_plate: dict[int, str], stem: str) -> int:
    matches = [palace for palace, value in earth_plate.items() if value == stem]
    if len(matches) != 1:
        raise ValueError(f"stem {stem} must occur exactly once on earth plate; got {matches}")
    return matches[0]


def _ring_index(palace: int) -> int:
    if palace == 5:
        palace = CENTER_HOST
    try:
        return RING.index(palace)
    except ValueError as exc:
        raise ValueError(f"palace not on rotating ring: {palace}") from exc


def _ring_shift(source: int, target: int) -> int:
    return (_ring_index(target) - _ring_index(source)) % len(RING)


def _rotate_home_map(home_map: dict[str, int], steps: int) -> dict[int, str]:
    result: dict[int, str] = {}
    for name, home in home_map.items():
        if home == 5:
            continue
        target = RING[(_ring_index(home) + steps) % len(RING)]
        if target in result:
            raise AssertionError(f"rotation collision at palace {target}")
        result[target] = name
    return result


def _duty_star_name(true_source_palace: int) -> str:
    for star, palace in STAR_HOME.items():
        if palace == true_source_palace:
            return star
    raise ValueError(f"no star home for palace {true_source_palace}")


def _duty_door_name(true_source_palace: int) -> str:
    effective = CENTER_HOST if true_source_palace == 5 else true_source_palace
    for door, palace in DOOR_HOME.items():
        if palace == effective:
            return door
    raise ValueError(f"no door home for effective source palace {effective}")


def _hour_target_stem(hour_pillar: str, xun: XunState) -> str:
    hour_stem = hour_pillar[0]
    return xun.hidden_instrument if hour_stem == "甲" else hour_stem


def _build_heaven_stars_and_stems(
    earth_plate: dict[int, str],
    star_steps: int,
) -> tuple[dict[int, tuple[str, ...]], dict[int, tuple[str, ...]]]:
    stars: dict[int, list[str]] = {p: [] for p in range(1, 10)}
    stems: dict[int, list[str]] = {p: [] for p in range(1, 10)}

    for star in PERIMETER_STARS:
        home = STAR_HOME[star]
        target = RING[(_ring_index(home) + star_steps) % len(RING)]
        stars[target].append(star)
        stems[target].append(earth_plate[home])
        if star == "天芮":
            stars[target].append("天禽")
            stems[target].append(earth_plate[5])

    return (
        {p: tuple(stars[p]) for p in range(1, 10)},
        {p: tuple(stems[p]) for p in range(1, 10)},
    )


def _build_doors(door_steps: int) -> dict[int, str]:
    return _rotate_home_map(DOOR_HOME, door_steps)


def _build_spirits(start_palace: int, dun: str) -> dict[int, str]:
    start_idx = _ring_index(start_palace)
    direction = 1 if dun == "阳" else -1
    result: dict[int, str] = {}
    for i, spirit in enumerate(SPIRIT_ORDER):
        palace = RING[(start_idx + direction * i) % len(RING)]
        result[palace] = spirit
    return result


def xunkong(pillar: str) -> tuple[tuple[str, ...], tuple[int, ...]]:
    if pillar not in JIAZI_INDEX:
        raise ValueError(f"invalid pillar: {pillar}")
    idx = JIAZI_INDEX[pillar]
    xun_start = (idx // 10) * 10
    branches = XUN_VOID[xun_start]
    palaces = tuple(sorted({BRANCH_PALACE[b] for b in branches}))
    return branches, palaces


def yima(hour_branch: str) -> tuple[str, int]:
    if hour_branch not in YIMA_BRANCH:
        raise ValueError(f"invalid hour branch: {hour_branch}")
    branch = YIMA_BRANCH[hour_branch]
    return branch, BRANCH_PALACE[branch]


def _integrity_checks(
    earth_plate: dict[int, str],
    stars: dict[int, tuple[str, ...]],
    heaven_stems: dict[int, tuple[str, ...]],
    doors: dict[int, str],
    spirits: dict[int, str],
) -> dict[str, bool]:
    flat_stars = [item for values in stars.values() for item in values]
    flat_stems = [item for values in heaven_stems.values() for item in values]
    checks = {
        "earth_plate_is_permutation": set(earth_plate.values()) == set(SANQI_LIUYI) and len(earth_plate) == 9,
        "stars_are_complete": set(flat_stars) == set(STAR_HOME) and len(flat_stars) == 9,
        "heaven_stems_are_complete": set(flat_stems) == set(SANQI_LIUYI) and len(flat_stems) == 9,
        "doors_are_complete": set(doors.values()) == set(DOOR_HOME) and set(doors) == set(RING),
        "spirits_are_complete": set(spirits.values()) == set(SPIRIT_ORDER) and set(spirits) == set(RING),
        "center_has_no_rotating_star": stars[5] == (),
        "center_has_no_heaven_stem": heaven_stems[5] == (),
        "center_has_no_door": 5 not in doors,
        "center_has_no_spirit": 5 not in spirits,
    }
    return checks


def build_qimen_plate(value: datetime | str) -> dict[str, object]:
    dt = _as_shanghai_datetime(value)
    pillars: Pillars = pillars_from_datetime(dt)
    term = current_solar_term(dt)
    ju = determine_ju(pillars.day, term.name)
    xun = determine_xun(pillars.time)
    earth = build_earth_plate(ju.dun, ju.ju)

    true_source = _palace_of_stem(earth, xun.hidden_instrument)
    effective_star_source = CENTER_HOST if true_source == 5 else true_source
    duty_star = _duty_star_name(true_source)
    duty_door = _duty_door_name(true_source)

    target_stem = _hour_target_stem(pillars.time, xun)
    target_true = _palace_of_stem(earth, target_stem)
    target_display = CENTER_HOST if target_true == 5 else target_true
    star_steps = _ring_shift(effective_star_source, target_display)
    stars, heaven_stems = _build_heaven_stars_and_stems(earth, star_steps)
    duty_star_display = target_display

    direction = 1 if ju.dun == "阳" else -1
    duty_door_raw = _numeric_palace(true_source, xun.hour_offset, direction)
    duty_door_display = CENTER_HOST if duty_door_raw == 5 else duty_door_raw
    effective_door_source = CENTER_HOST if true_source == 5 else true_source
    door_steps = _ring_shift(effective_door_source, duty_door_display)
    doors = _build_doors(door_steps)
    spirits = _build_spirits(duty_star_display, ju.dun)

    day_void_branches, day_void_palaces = xunkong(pillars.day)
    hour_void_branches, hour_void_palaces = xunkong(pillars.time)
    yima_branch, yima_palace = yima(pillars.time_branch)

    integrity = _integrity_checks(earth, stars, heaven_stems, doors, spirits)
    if not all(integrity.values()):
        failed = [k for k, ok in integrity.items() if not ok]
        raise AssertionError(f"QIMEN_V1 plate integrity failed: {failed}")

    palace_rows: dict[int, dict[str, object]] = {}
    for palace in range(1, 10):
        trigram, direction_name = PALACE_META[palace]
        palace_rows[palace] = {
            "trigram": trigram,
            "direction": direction_name,
            "earth_stem": earth[palace],
            "heaven_stars": stars[palace],
            "heaven_stems": heaven_stems[palace],
            "door": doors.get(palace, ""),
            "spirit": spirits.get(palace, ""),
            "day_void": int(palace in day_void_palaces),
            "hour_void": int(palace in hour_void_palaces),
            "yima": int(palace == yima_palace),
        }

    return {
        "engine_id": "QIMEN_V1",
        "engine_version": 1,
        "convention": {
            "plate_type": "rotating",
            "ju_method": "chai_bu",
            "yuan_method": "day_jiazi_index_five_day_blocks",
            "timezone": "Asia/Shanghai",
            "center_host_palace": CENTER_HOST,
            "solar_term_whole_day": False,
            "aggregate_score_defined": False,
        },
        "datetime": dt.isoformat(),
        "pillars": {
            "year": pillars.year,
            "month": pillars.month,
            "day": pillars.day,
            "time": pillars.time,
        },
        "solar_term": {
            "name": term.name,
            "timestamp": term.timestamp.isoformat(),
        },
        "ju": {
            "dun": ju.dun,
            "number": ju.ju,
            "yuan_index": ju.yuan_index,
            "yuan": ju.yuan,
            "day_index": ju.day_index,
            "fu_head_index": ju.fu_head_index,
            "fu_head": ju.fu_head,
        },
        "xun": {
            "xunshou": xun.xunshou,
            "hidden_instrument": xun.hidden_instrument,
            "hour_index": xun.hour_index,
            "xun_start_index": xun.xun_start_index,
            "hour_offset": xun.hour_offset,
            "true_source_palace": true_source,
            "effective_star_source_palace": effective_star_source,
        },
        "duty": {
            "star": duty_star,
            "star_true_source_palace": true_source,
            "star_display_palace": duty_star_display,
            "door": duty_door,
            "door_true_source_palace": true_source,
            "door_raw_destination_palace": duty_door_raw,
            "door_display_palace": duty_door_display,
            "hour_target_stem": target_stem,
            "hour_target_true_palace": target_true,
            "hour_target_display_palace": target_display,
            "star_steps": star_steps,
            "door_steps": door_steps,
        },
        "states": {
            "star_fuyin": int(star_steps == 0),
            "star_fanyin": int(star_steps == 4),
            "day_xunkong_branches": day_void_branches,
            "day_xunkong_palaces": day_void_palaces,
            "hour_xunkong_branches": hour_void_branches,
            "hour_xunkong_palaces": hour_void_palaces,
            "yima_branch": yima_branch,
            "yima_palace": yima_palace,
        },
        "earth_plate": earth,
        "heaven_stars": stars,
        "heaven_stems": heaven_stems,
        "doors": doors,
        "spirits": spirits,
        "palaces": palace_rows,
        "integrity": integrity,
    }
