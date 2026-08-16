from metaalpha.zpzt_structure_v4 import structure_features_from_pillars


def test_source_bad_wealth_resource_example_is_adjacent():
    # 《论财》反例：乙未 己卯 庚寅 辛巳。乙财与己印在年/月干直接相并，原文判两不相能。
    f = structure_features_from_pillars("乙未", "己卯", "庚寅", "辛巳")
    assert f["zpzt_structure__v4__wealth_positions"] == "0"
    assert f["zpzt_structure__v4__resource_positions"] == "1"
    assert f["zpzt_structure__v4__wealth_resource_min_distance"] == 1
    assert f["zpzt_structure__v4__wealth_resource_position_state"] == "adjacent_only"
    assert f["zpzt_structure__v4__wealth_resource_position_resolution"] == "position_condition_blocked"


def test_source_good_wealth_resource_example_is_separated():
    # 《论财》曾参政例：乙未 甲申 丙申 庚寅。财印双清且隔离；乙/甲印在前，庚财在时干。
    f = structure_features_from_pillars("乙未", "甲申", "丙申", "庚寅")
    assert f["zpzt_structure__v4__wealth_positions"] == "3"
    assert f["zpzt_structure__v4__resource_positions"] == "0|1"
    assert f["zpzt_structure__v4__wealth_resource_min_distance"] == 2
    assert f["zpzt_structure__v4__wealth_resource_position_state"] == "separated_only"
    assert f["zpzt_structure__v4__wealth_resource_position_resolution"] == "position_condition_satisfied"


def test_visible_resource_root_is_recorded_without_strength_score():
    # 癸为甲日主之印；地支子藏癸，因此这里能机械确认“印有根”证据，但不推出身强分值。
    f = structure_features_from_pillars("癸子", "丙午", "甲辰", "丁酉")
    assert f["zpzt_structure__v4__resource_visible_count"] >= 1
    assert f["zpzt_structure__v4__resource_rooted_visible_count"] >= 1
    assert f["zpzt_structure__v4__aggregate_strength_score_defined"] == 0
    assert f["zpzt_structure__v4__aggregate_fortune_score_defined"] == 0


def test_support_profile_is_categorical_raw_evidence_not_score():
    f = structure_features_from_pillars("甲寅", "癸亥", "甲子", "乙卯")
    profile = f["zpzt_structure__v4__support_profile"]
    assert "dmroot_" in profile
    assert "visible_" in profile
    assert f["zpzt_structure__v4__daymaster_exact_root_count"] >= 1
    assert f["zpzt_structure__v4__aggregate_strength_score_defined"] == 0
