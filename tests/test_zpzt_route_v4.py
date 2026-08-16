from metaalpha.zpzt_route_v4 import refined_route_features_from_pillars


def test_good_source_wealth_resource_position_resolves_route():
    f = refined_route_features_from_pillars("乙未", "甲申", "丙申", "庚寅")
    assert f["zpzt_route__v4__wealth_resource_position_resolution"] == "position_condition_satisfied"
    assert "wealth_resource_position_route" in f["zpzt_route__v4__route_hits"]
    assert "wealth_resource_position_route" not in f["zpzt_route__v4__route_unresolved"]
    assert f["zpzt_route__v4__resolved_from_position_count"] == 1


def test_bad_source_wealth_resource_position_blocks_route():
    f = refined_route_features_from_pillars("乙未", "己卯", "庚寅", "辛巳")
    assert f["zpzt_route__v4__wealth_resource_position_resolution"] == "position_condition_blocked"
    assert "wealth_resource_position_route" in f["zpzt_route__v4__route_blocked"]
    assert "wealth_resource_position_route" not in f["zpzt_route__v4__route_unresolved"]
    assert f["zpzt_route__v4__route_blocked_count"] == 1


def test_v4_does_not_resolve_strength_or_quantity():
    f = refined_route_features_from_pillars("丁卯", "癸酉", "乙丑", "戊寅")
    assert f["zpzt_route__v4__strength_resolution_applied"] == 0
    assert f["zpzt_route__v4__quantity_resolution_applied"] == 0
    assert f["zpzt_route__v4__aggregate_score_defined"] == 0
