from metaalpha.zpzt_use_v2 import month_use_features_from_pillars


def test_shen_month_secondary_transmission_changes_hurting_to_wealth():
    # 《子平真诠》 example structure: 己生申月，本属伤官；庚不透而壬透，转以财为显用候选。
    f = month_use_features_from_pillars("壬子", "乙申", "己卯", "丁巳")
    assert f["zpzt_use__v2__primary_ten_god"] == "伤官"
    assert f["zpzt_use__v2__primary_transmitted"] == 0
    assert f["zpzt_use__v2__selected_stem"] == "壬"
    assert f["zpzt_use__v2__selected_ten_god"] == "正财"
    assert f["zpzt_use__v2__selection_mode"] == "secondary_transmitted"
    assert f["zpzt_use__v2__transmission_changes_main"] == 1


def test_yin_month_secondary_bing_changes_wealth_to_official():
    # 辛生寅月：甲为本主；甲不透、丙透时，丙可作主，财转官候选。
    f = month_use_features_from_pillars("丙子", "乙寅", "辛卯", "丁巳")
    assert f["zpzt_use__v2__primary_stem"] == "甲"
    assert f["zpzt_use__v2__primary_ten_god"] == "正财"
    assert f["zpzt_use__v2__selected_stem"] == "丙"
    assert f["zpzt_use__v2__selected_ten_god"] == "正官"
    assert f["zpzt_use__v2__selected_pattern_candidate"] == "官格"


def test_primary_transmission_keeps_primary_when_primary_and_secondary_both_visible():
    # 原文另举辛生寅月甲、丙并透：本格财仍在，官作兼格。v2 因而不让次气覆盖已透本气。
    f = month_use_features_from_pillars("甲子", "丙寅", "辛卯", "丁巳")
    assert f["zpzt_use__v2__primary_transmitted"] == 1
    assert f["zpzt_use__v2__transmitted_count"] == 2
    assert f["zpzt_use__v2__selected_stem"] == "甲"
    assert f["zpzt_use__v2__selected_ten_god"] == "正财"
    assert f["zpzt_use__v2__composition_mode"] == "multiple_transmitted"
    assert f["zpzt_use__v2__mixed_families"] == 1


def test_chen_mixed_month_uses_transmitted_gui_when_primary_not_visible():
    # 杂气例：甲生辰月，透癸则用正印。
    f = month_use_features_from_pillars("癸子", "丙辰", "甲午", "丁酉")
    assert f["zpzt_use__v2__month_hidden_stems"] == "戊乙癸"
    assert f["zpzt_use__v2__selected_stem"] == "癸"
    assert f["zpzt_use__v2__selected_ten_god"] == "正印"
    assert f["zpzt_use__v2__selected_pattern_candidate"] == "印格"


def test_full_three_harmony_records_branch_use_change_without_inventing_polarity():
    # 丁生亥月，支全卯未：原文作官化印。这里只编码木局=>resource family，
    # 不武断指定正印/偏印，因为会支给的是元素局而非单一阴阳天干。
    f = month_use_features_from_pillars("乙卯", "辛亥", "丁未", "己子")
    assert f["zpzt_use__v2__primary_ten_god"] == "正官"
    assert f["zpzt_use__v2__harmony_element"] == "木"
    assert f["zpzt_use__v2__harmony_family"] == "resource"
    assert f["zpzt_use__v2__harmony_changes_family"] == 1
    assert f["zpzt_use__v2__use_change_detected"] == 1
    assert f["zpzt_use__v2__aggregate_fortune_score_defined"] == 0
