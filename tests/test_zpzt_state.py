from metaalpha.zpzt_state import evaluate_provisional_state


def test_official_pattern_can_form_with_wealth_resource_and_no_disruption():
    # 戊辰 辛酉 甲寅 癸丑
    # 甲日主，酉月本气辛为正官；戊财、癸印透。
    state = evaluate_provisional_state("戊辰", "辛酉", "甲寅", "癸丑")
    assert state.formation is True
    assert state.failure is False
    assert state.state.startswith("成候选")


def test_official_pattern_hurting_official_with_resource_is_rescue_candidate():
    # 丁丑 辛酉 甲寅 癸亥
    # 丁为伤官，癸为正印：对应“官逢伤而透印以解之”的机器化候选。
    state = evaluate_provisional_state("丁丑", "辛酉", "甲寅", "癸亥")
    assert state.failure is True
    assert state.rescue is True
    assert state.state.startswith("败中有救候选")


def test_yang_blade_without_official_or_killings_is_failure_candidate():
    # 甲日主卯月 -> registered 阳刃 condition; visible stems contain no 官杀.
    state = evaluate_provisional_state("壬子", "乙卯", "甲寅", "丙寅")
    assert state.failure is True
    assert "败候选" in state.state


def test_strength_dependent_rule_is_not_forced_into_final_binary_judgment():
    # 印格 is intentionally marked as requiring a separate strength layer.
    state = evaluate_provisional_state("庚子", "壬申", "丙寅", "甲午")
    if state.requires_strength:
        assert state.state.endswith("_待强弱层")
