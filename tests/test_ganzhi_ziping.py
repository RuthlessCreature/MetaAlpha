import pandas as pd

from metaalpha.bazi_ziping import (
    HIDDEN_STEMS,
    features_from_pillars,
    pattern_from_month_command,
    ten_god,
)
from metaalpha.ganzhi import pillars_from_datetime
from metaalpha.pipeline import build_dataset


def test_reference_calendar_example_from_lunar_python_readme():
    # The upstream lunar-python README shows 1986-05-29 as
    # 丙寅 year, 癸巳 month, 癸酉 day. MetaAlpha uses a 09:25 market
    # anchor, which changes only the time pillar for this date.
    p = pillars_from_datetime("1986-05-29")
    assert p.year == "丙寅"
    assert p.month == "癸巳"
    assert p.day == "癸酉"


def test_ten_gods_for_jia_day_master_cover_all_ten():
    expected = {
        "甲": "比肩",
        "乙": "劫财",
        "丙": "食神",
        "丁": "伤官",
        "戊": "偏财",
        "己": "正财",
        "庚": "七杀",
        "辛": "正官",
        "壬": "偏印",
        "癸": "正印",
    }
    assert {s: ten_god("甲", s) for s in expected} == expected


def test_hidden_stem_principal_qi_is_first_and_registered():
    assert HIDDEN_STEMS["酉"][0] == "辛"
    assert HIDDEN_STEMS["寅"] == ("甲", "丙", "戊")
    assert HIDDEN_STEMS["丑"] == ("己", "癸", "辛")


def test_pattern_candidate_uses_month_command_and_yang_blade_override():
    assert pattern_from_month_command("甲", "酉").candidate == "官格"
    assert pattern_from_month_command("甲", "卯").candidate == "阳刃格"
    assert pattern_from_month_command("乙", "卯").candidate == "建禄月劫"


def test_month_clash_is_machine_readable():
    # Month 午 clashes with year 子.
    f = features_from_pillars("甲子", "庚午", "甲申", "庚午")
    assert f["zpzt__v1__month_clash"] == 1
    assert f["zpzt__v1__month_command"] == "午"


def test_pipeline_can_enable_ziping_features():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-02", periods=30, freq="B"),
            "close": [3000 + i for i in range(30)],
        }
    )
    out = build_dataset(df, include_ziping=True)
    assert "ganzhi__v2__day_pillar" in out.columns
    assert "zpzt__v1__pattern_candidate" in out.columns
    assert "ret_fwd_1" in out.columns
