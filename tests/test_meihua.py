from metaalpha.meihua import features_for_datetime, plate_for_datetime


def test_meihua_traditional_time_example_2017_01_14_10am():
    # Published example: lunar 丙申年十二月十七日巳时.
    # (申=9) + 12 + 17 = 38 -> 余6? Note: the commonly published worked
    # example that gives 震/兑 uses year number 7, which is inconsistent with
    # the stated 子1..亥12 sequence for 申=9. This test therefore verifies our
    # preregistered arithmetic convention itself rather than copying that
    # internally inconsistent arithmetic.
    p = plate_for_datetime("2017-01-14 10:00:00")
    assert p.lunar_year_branch == "申"
    assert p.lunar_month == 12
    assert p.lunar_day == 17
    assert p.time_branch == "巳"
    # Frozen formula with 申=9: 9+12+17=38 => 余6 坎;
    # +巳6=44 => 余4 震; 44 mod 6 => 二爻动.
    assert p.upper_trigram == "坎"
    assert p.lower_trigram == "震"
    assert p.moving_line == 2


def test_meihua_feature_state_has_no_fortune_score():
    f = features_for_datetime("2026-08-17 09:25:00")
    assert f["meihua__v1__fortune_score_defined"] == 0
    assert f["meihua__v1__moving_line"] in {1, 2, 3, 4, 5, 6}
    assert f["meihua__v1__body_use_relation"] in {"比和", "体生用", "用生体", "体克用", "用克体"}
    assert len(f["meihua__v1__base_line_pattern"]) == 6
    assert len(f["meihua__v1__changed_line_pattern"]) == 6
