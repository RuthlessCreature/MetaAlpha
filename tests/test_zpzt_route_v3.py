from metaalpha.zpzt_route_v3 import route_graph_from_pillars


def test_official_resource_combines_hurting_source_route():
    # 甲用酉官，透丁逢壬：丁伤官、壬偏印，丁壬合，机械上形成“合伤存官”候选。
    f = route_graph_from_pillars("壬子", "丁酉", "甲辰", "丙寅")
    assert f["zpzt_route__v3__base_pattern"] == "官格"
    assert "official_resource_protects_use" in f["zpzt_route__v3__route_hits"]
    assert "official_resource_combines_hurting_rescue" in f["zpzt_route__v3__route_hits"]
    assert f["zpzt_route__v3__source_example_rescue_hit_count"] >= 1


def test_wealth_robwealth_combines_killing_source_route():
    # 戊用子财，透甲并己：甲七杀、己劫财，甲己合，机械上形成“合杀存财”候选。
    f = route_graph_from_pillars("甲寅", "己子", "戊辰", "丙午")
    assert f["zpzt_route__v3__base_pattern"] == "财格"
    assert "wealth_robwealth_combines_killing_rescue" in f["zpzt_route__v3__route_hits"]
    assert f["zpzt_route__v3__source_example_rescue_hit_count"] >= 1


def test_killing_food_route_records_combined_resource_rescue_as_unresolved_strength():
    # 乙用酉杀，丁食、癸偏印、戊财；戊癸合，使食神制杀路径重新可用。
    # 杀格“身强”仍不由任意分数解决，因此这条源例路径应存在但保留 strength 未决。
    f = route_graph_from_pillars("丁卯", "癸酉", "乙丑", "戊寅")
    assert f["zpzt_route__v3__base_pattern"] == "七杀格"
    assert "killing_food_controls_use" in f["zpzt_route__v3__route_unresolved"]
    assert "killing_food_released_by_combining_resource" in f["zpzt_route__v3__route_unresolved"]
    assert f["zpzt_route__v3__source_example_route_present_count"] >= 1
    assert f["zpzt_route__v3__requires_strength_route_count"] >= 1


def test_month_peer_harmony_output_generates_visible_wealth():
    # 癸生亥月为月劫；卯亥未会木（输出），同时丙财透出。会局先改变用神家族，
    # 因此不能再把变化前月劫的普通“财+食伤”路线与会局路线同时重复计算。
    f = route_graph_from_pillars("庚卯", "丙亥", "癸未", "己巳")
    assert f["zpzt_route__v3__base_pattern"] == "建禄月劫"
    assert f["zpzt_route__v3__harmony_family"] == "output"
    assert f["zpzt_route__v3__effective_use_scope"] == "family_only_from_harmony"
    assert f["zpzt_route__v3__harmony_transition_only"] == 1
    assert f["zpzt_route__v3__downstream_polarity_unresolved"] == 1
    assert "harmony_transforms_month_use_family" in f["zpzt_route__v3__route_hits"]
    assert "peer_harmony_output_generates_wealth" in f["zpzt_route__v3__route_hits"]
    assert "peer_wealth_with_output" not in f["zpzt_route__v3__route_hits"]
    assert f["zpzt_route__v3__source_example_rescue_hit_count"] >= 1


def test_official_harmony_to_resource_does_not_apply_old_official_routes():
    # 丁生亥月，卯亥未会木。月令壬水原为官，但完整木局先把有效用神家族转为资源。
    # 会局只给元素家族，不给正偏极性，所以旧官格相神路线必须停止。
    f = route_graph_from_pillars("乙卯", "辛亥", "丁未", "己子")
    assert f["zpzt_route__v3__base_pattern"] == "官格"
    assert f["zpzt_route__v3__harmony_family"] == "resource"
    assert f["zpzt_route__v3__effective_use_family"] == "resource"
    assert f["zpzt_route__v3__effective_use_scope"] == "family_only_from_harmony"
    assert "harmony_transforms_month_use_family" in f["zpzt_route__v3__route_hits"]
    assert "official_harmony_transforms_to_resource" in f["zpzt_route__v3__route_hits"]
    assert "official_wealth_generates_use" not in f["zpzt_route__v3__route_hits"]
    assert "official_resource_protects_use" not in f["zpzt_route__v3__route_hits"]


def test_route_v3_never_defines_aggregate_score():
    f = route_graph_from_pillars("壬子", "丁酉", "甲辰", "丙寅")
    assert f["zpzt_route__v3__aggregate_score_defined"] == 0
