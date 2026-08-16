import pandas as pd

from metaalpha.natal_transit import (
    SSE_NATAL_V1,
    add_sse_natal_transit_features,
    features_for_transit_datetime,
    natal_pillars,
    natal_static_features,
)


def test_sse_natal_anchor_is_frozen_to_official_opening_gong_time():
    assert SSE_NATAL_V1.anchor.strftime("%Y-%m-%d %H:%M") == "1990-12-19 11:00"
    assert str(SSE_NATAL_V1.anchor.tzinfo) == "Asia/Shanghai"


def test_natal_static_features_are_deterministic_and_complete():
    a = natal_static_features()
    b = natal_static_features()
    assert a == b
    assert a["natal__v1__chart_id"] == "SSE_NATAL_V1"
    assert len(a["natal__v1__day_pillar"]) == 2
    assert a["natal__v1__use_mode"] in {"顺用", "逆用"}


def test_transit_features_encode_relations_without_fortune_score():
    f = features_for_transit_datetime("2026-08-14")
    assert f["natal_transit__v1__fortune_score_defined"] == 0
    assert f["natal_transit__v1__day_stem_ten_god"] in {
        "比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印"
    }
    for key in (
        "natal_transit__v1__stem_combine_count",
        "natal_transit__v1__branch_clash_count",
        "natal_transit__v1__branch_harm_count",
        "natal_transit__v1__branch_break_count",
        "natal_transit__v1__branch_six_combine_count",
        "natal_transit__v1__disruption_relation_count",
    ):
        assert f[key] >= 0


def test_dataframe_adapter_preserves_rows_and_adds_natal_columns():
    df = pd.DataFrame({"date": ["2026-08-13", "2026-08-14"], "close": [1.0, 1.1]})
    out = add_sse_natal_transit_features(df)
    assert len(out) == 2
    assert "natal__v1__day_pillar" in out.columns
    assert "natal_transit__v1__day_clashes_natal_day" in out.columns
    assert out["natal__v1__chart_id"].nunique() == 1


def test_natal_pillars_use_exact_11am_anchor_not_market_default():
    p = natal_pillars()
    assert len(p.time) == 2
