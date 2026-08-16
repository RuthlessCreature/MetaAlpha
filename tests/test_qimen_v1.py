from datetime import datetime
from zoneinfo import ZoneInfo

from metaalpha.qimen_v1 import (
    TZ_SHANGHAI,
    build_earth_plate,
    build_qimen_plate,
    current_solar_term,
    determine_ju,
)


def test_chai_bu_day_index_yuan_rule():
    xiaoshu = determine_ju("甲申", "小暑")
    assert xiaoshu.day_index == 20
    assert xiaoshu.fu_head == "甲申"
    assert xiaoshu.yuan == "中元"
    assert xiaoshu.dun == "阴"
    assert xiaoshu.ju == 2

    dongzhi = determine_ju("乙亥", "冬至")
    assert dongzhi.day_index == 11
    assert dongzhi.fu_head == "甲戌"
    assert dongzhi.yuan == "下元"
    assert dongzhi.dun == "阳"
    assert dongzhi.ju == 4


def test_earth_plate_yin_two_and_yang_four():
    assert build_earth_plate("阴", 2) == {
        1: "己", 2: "戊", 3: "乙", 4: "丙", 5: "丁",
        6: "癸", 7: "壬", 8: "辛", 9: "庚",
    }
    assert build_earth_plate("阳", 4) == {
        1: "丁", 2: "丙", 3: "乙", 4: "戊", 5: "己",
        6: "庚", 7: "辛", 8: "壬", 9: "癸",
    }


def test_golden_plate_2026_07_09_1030_yin_two_middle_yuan():
    plate = build_qimen_plate("2026-07-09T10:30:00+08:00")

    assert plate["pillars"] == {"year": "丙午", "month": "乙未", "day": "甲申", "time": "己巳"}
    assert plate["solar_term"]["name"] == "小暑"
    assert plate["solar_term"]["timestamp"] == "2026-07-07T09:56:57+08:00"
    assert plate["ju"] == {
        "dun": "阴",
        "number": 2,
        "yuan_index": 1,
        "yuan": "中元",
        "day_index": 20,
        "fu_head_index": 20,
        "fu_head": "甲申",
    }
    assert plate["xun"]["xunshou"] == "甲子"
    assert plate["xun"]["hidden_instrument"] == "戊"
    assert plate["xun"]["true_source_palace"] == 2

    assert plate["duty"]["star"] == "天芮"
    assert plate["duty"]["star_display_palace"] == 1
    assert plate["duty"]["door"] == "死门"
    assert plate["duty"]["door_raw_destination_palace"] == 6
    assert plate["duty"]["door_display_palace"] == 6
    assert plate["duty"]["star_steps"] == 3
    assert plate["duty"]["door_steps"] == 2

    assert plate["earth_plate"] == {
        1: "己", 2: "戊", 3: "乙", 4: "丙", 5: "丁",
        6: "癸", 7: "壬", 8: "辛", 9: "庚",
    }
    assert plate["heaven_stars"] == {
        1: ("天芮", "天禽"),
        2: ("天冲",),
        3: ("天心",),
        4: ("天蓬",),
        5: (),
        6: ("天英",),
        7: ("天辅",),
        8: ("天柱",),
        9: ("天任",),
    }
    assert plate["heaven_stems"] == {
        1: ("戊", "丁"),
        2: ("乙",),
        3: ("癸",),
        4: ("己",),
        5: (),
        6: ("庚",),
        7: ("丙",),
        8: ("壬",),
        9: ("辛",),
    }
    assert plate["doors"] == {
        1: "惊门", 2: "杜门", 3: "休门", 4: "生门",
        6: "死门", 7: "景门", 8: "开门", 9: "伤门",
    }
    assert plate["spirits"] == {
        1: "值符", 2: "六合", 3: "九地", 4: "玄武",
        6: "螣蛇", 7: "太阴", 8: "九天", 9: "白虎",
    }
    assert plate["states"]["star_fuyin"] == 0
    assert plate["states"]["star_fanyin"] == 0
    assert plate["states"]["day_xunkong_branches"] == ("午", "未")
    assert plate["states"]["day_xunkong_palaces"] == (2, 9)
    assert plate["states"]["hour_xunkong_branches"] == ("戌", "亥")
    assert plate["states"]["hour_xunkong_palaces"] == (6,)
    assert plate["states"]["yima_branch"] == "亥"
    assert plate["states"]["yima_palace"] == 6
    assert all(plate["integrity"].values())
    assert plate["convention"]["aggregate_score_defined"] is False


def test_golden_plate_2026_01_01_1200_center_xunshou_yang_four_lower_yuan():
    plate = build_qimen_plate("2026-01-01T12:00:00+08:00")

    assert plate["pillars"] == {"year": "乙巳", "month": "戊子", "day": "乙亥", "time": "壬午"}
    assert plate["solar_term"]["name"] == "冬至"
    assert plate["solar_term"]["timestamp"] == "2025-12-21T23:03:05+08:00"
    assert plate["ju"]["dun"] == "阳"
    assert plate["ju"]["number"] == 4
    assert plate["ju"]["yuan"] == "下元"
    assert plate["ju"]["fu_head"] == "甲戌"

    assert plate["xun"]["xunshou"] == "甲戌"
    assert plate["xun"]["hidden_instrument"] == "己"
    assert plate["xun"]["true_source_palace"] == 5
    assert plate["xun"]["effective_star_source_palace"] == 2

    assert plate["duty"]["star"] == "天禽"
    assert plate["duty"]["star_true_source_palace"] == 5
    assert plate["duty"]["star_display_palace"] == 8
    assert plate["duty"]["door"] == "死门"
    assert plate["duty"]["door_true_source_palace"] == 5
    assert plate["duty"]["door_raw_destination_palace"] == 4
    assert plate["duty"]["door_display_palace"] == 4
    assert plate["duty"]["star_steps"] == 4
    assert plate["duty"]["door_steps"] == 6

    assert plate["heaven_stars"] == {
        1: ("天英",),
        2: ("天任",),
        3: ("天柱",),
        4: ("天心",),
        5: (),
        6: ("天辅",),
        7: ("天冲",),
        8: ("天芮", "天禽"),
        9: ("天蓬",),
    }
    assert plate["heaven_stems"] == {
        1: ("癸",),
        2: ("壬",),
        3: ("辛",),
        4: ("庚",),
        5: (),
        6: ("戊",),
        7: ("乙",),
        8: ("丙", "己"),
        9: ("丁",),
    }
    assert plate["doors"] == {
        1: "伤门", 2: "开门", 3: "景门", 4: "死门",
        6: "生门", 7: "休门", 8: "杜门", 9: "惊门",
    }
    assert plate["spirits"] == {
        1: "九天", 2: "白虎", 3: "螣蛇", 4: "太阴",
        6: "九地", 7: "玄武", 8: "值符", 9: "六合",
    }
    assert plate["states"]["star_fuyin"] == 0
    assert plate["states"]["star_fanyin"] == 1
    assert plate["states"]["day_xunkong_branches"] == ("申", "酉")
    assert plate["states"]["day_xunkong_palaces"] == (2, 7)
    assert plate["states"]["hour_xunkong_branches"] == ("申", "酉")
    assert plate["states"]["hour_xunkong_palaces"] == (2, 7)
    assert plate["states"]["yima_branch"] == "申"
    assert plate["states"]["yima_palace"] == 2
    assert all(plate["integrity"].values())


def test_exact_solar_term_boundary_not_whole_day():
    before = current_solar_term("2025-12-21T10:00:00+08:00")
    after = current_solar_term("2025-12-21T23:30:00+08:00")
    assert before.name == "大雪"
    assert after.name == "冬至"
    assert before.timestamp < datetime(2025, 12, 21, 10, 0, tzinfo=TZ_SHANGHAI)
    assert after.timestamp <= datetime(2025, 12, 21, 23, 30, tzinfo=TZ_SHANGHAI)
    assert after.timestamp > datetime(2025, 12, 21, 10, 0, tzinfo=TZ_SHANGHAI)
