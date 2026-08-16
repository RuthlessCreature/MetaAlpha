import numpy as np
import pandas as pd

from metaalpha.research_natal import fake_natal_specs, run_historical_exploration


def test_fake_natal_specs_are_frozen_and_distinct():
    specs = fake_natal_specs()
    assert [x.id for x in specs] == [
        "SSE_FAKE_NATAL_P17",
        "SSE_FAKE_NATAL_P31",
        "SSE_FAKE_NATAL_P47",
    ]
    assert len({x.anchor for x in specs}) == 3


def test_natal_exploration_emits_real_shift_and_fake_controls(tmp_path):
    dates = pd.bdate_range("2018-01-02", periods=420)
    close = 3000.0 * np.exp(np.linspace(0.0, 0.06, len(dates)))
    raw = pd.DataFrame(
        {
            "symbol": "INDEX_TEST",
            "date": dates,
            "open": close * 0.999,
            "high": close * 1.004,
            "low": close * 0.996,
            "close": close,
            "volume": np.arange(len(dates)) + 1000,
        }
    )

    result = run_historical_exploration(raw, out_dir=tmp_path, min_n=5)
    assert len(result["dataset"]) == len(raw)
    assert not result["screen"].empty
    kinds = set(result["screen"]["test_kind"])
    assert {"registered_real_natal", "shift_null", "fake_natal"}.issubset(kinds)
    assert (tmp_path / "historical_exploratory_screen.csv").exists()
    assert (tmp_path / "diagnostic_summary.csv").exists()
    assert (tmp_path / "run_metadata.json").exists()
    assert (tmp_path / "SUMMARY.md").exists()
