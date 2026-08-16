import pandas as pd

from metaalpha.qimen_market import add_qimen_market_features, qimen_market_features_for_date


def test_market_features_use_frozen_0925_plate_and_no_score():
    f = qimen_market_features_for_date("2026-08-17")
    assert f["qimen__v1__engine_id"] == "QIMEN_V1"
    assert f["qimen__v1__aggregate_score_defined"] == 0
    assert f["qimen__v1__dun"] in {"阳", "阴"}
    assert f["qimen__v1__yuan"] in {"上元", "中元", "下元"}
    assert 1 <= f["qimen__v1__ju_number"] <= 9
    assert f["qimen__v1__duty_star"]
    assert f["qimen__v1__duty_door"]


def test_relation_states_are_mechanical_categorical_encodings():
    f = qimen_market_features_for_date("2026-01-01")
    assert f["qimen__v1__star_state"] in {"伏吟", "反吟", "常态"}
    assert "source=" in f["qimen__v1__xun_target_state"]
    assert "day_star=" in f["qimen__v1__void_relation_state"]
    assert "palace=" in f["qimen__v1__yima_relation_state"]
    assert "star=" in f["qimen__v1__duty_door_palace_composition"]
    assert "door=" in f["qimen__v1__yima_palace_composition"]


def test_dataframe_adapter_preserves_rows():
    raw = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-08-17", "2026-08-18", "2026-08-19"]),
            "close": [100.0, 101.0, 99.0],
        }
    )
    out = add_qimen_market_features(raw)
    assert len(out) == 3
    assert "qimen__v1__dun_ju_yuan" in out.columns
    assert "qimen__v1__duty_star_door" in out.columns
    assert "qimen__v1__rotation_state" in out.columns
