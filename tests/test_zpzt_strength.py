from metaalpha.zpzt_strength import strength_primitives_from_pillars


def test_strength_layer_exposes_primitives_not_master_score():
    f = strength_primitives_from_pillars("辛未", "庚子", "癸酉", "乙卯")
    assert f["zpzt_strength__v1__day_master_element"] == "水"
    assert f["zpzt_strength__v1__month_element"] == "水"
    assert f["zpzt_strength__v1__month_relation"] == "same"
    assert f["zpzt_strength__v1__month_supports_daymaster"] == 1
    assert f["zpzt_strength__v1__aggregate_score_defined"] == 0


def test_exact_roots_are_counted_from_hidden_stems():
    # 癸日主: 子藏癸, 丑藏癸, 辰藏癸, so exact roots should be visible to the primitive layer.
    f = strength_primitives_from_pillars("甲子", "乙丑", "癸卯", "丙辰")
    assert f["zpzt_strength__v1__exact_root_count"] == 3
