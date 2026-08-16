import numpy as np
import pandas as pd

from metaalpha.calendar_cycle import JIE_QI_INDEX, add_calendar_cycle_features, cycle_features_for_datetime
from metaalpha.ganzhi import pillars_from_datetime


def test_mid_july_2022_is_between_xiaoshu_and_dashu():
    f = cycle_features_for_datetime("2022-07-15")
    assert f["cycle__v1__prev_jieqi"] == "小暑"
    assert f["cycle__v1__next_jieqi"] == "大暑"
    assert 0.0 < f["cycle__v1__jieqi_phase"] < 1.0
    assert f["cycle__v1__jieqi_phase_quartile"] in {0, 1, 2, 3}
    assert f["cycle__v1__prev_jieqi_index"] == JIE_QI_INDEX["小暑"]


def test_cycle_day_fields_match_frozen_ganzhi_engine():
    f = cycle_features_for_datetime("2026-08-17")
    p = pillars_from_datetime("2026-08-17")
    assert f["cycle__v1__day_pillar"] == p.day
    assert f["cycle__v1__day_stem"] == p.day_stem
    assert f["cycle__v1__day_branch"] == p.day_branch
    assert f["cycle__v1__month_stem"] == p.month_stem
    assert f["cycle__v1__month_branch"] == p.month_branch


def test_solar_term_sin_cos_are_normalized_cycle_coordinates():
    f = cycle_features_for_datetime("2026-08-17")
    r2 = f["cycle__v1__term_phase_sin"] ** 2 + f["cycle__v1__term_phase_cos"] ** 2
    assert np.isclose(r2, 1.0)


def test_dataframe_adapter_adds_cycle_columns():
    raw = pd.DataFrame({"date": ["2026-08-17", "2026-08-18"], "close": [100.0, 101.0]})
    out = add_calendar_cycle_features(raw)
    assert len(out) == 2
    assert "cycle__v1__prev_jieqi" in out.columns
    assert "cycle__v1__jieqi_phase" in out.columns
    assert out["cycle__v1__jieqi_phase"].between(0.0, 1.0).all()
