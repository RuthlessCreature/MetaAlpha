import numpy as np
import pandas as pd

from metaalpha.research_ziping import run_first_sse_experiment


def test_first_experiment_writes_registered_and_null_outputs(tmp_path):
    dates = pd.bdate_range("2012-01-03", periods=260)
    close = 2000.0 * np.exp(np.linspace(0.0, 0.08, len(dates)))
    raw = pd.DataFrame(
        {
            "symbol": "INDEX_TEST",
            "date": dates,
            "open": close * 0.999,
            "high": close * 1.005,
            "low": close * 0.995,
            "close": close,
            "volume": np.arange(len(dates)) + 1000,
        }
    )

    result = run_first_sse_experiment(raw, out_dir=tmp_path, min_n=5)

    assert len(result["dataset"]) == len(raw)
    assert not result["screen"].empty
    assert {"registered", "shift_null"}.issubset(set(result["screen"]["test_kind"]))
    assert (tmp_path / "dataset.csv").exists()
    assert (tmp_path / "registered_and_null_screens.csv").exists()
    assert (tmp_path / "diagnostic_summary.csv").exists()
    assert (tmp_path / "run_metadata.json").exists()
    assert (tmp_path / "SUMMARY.md").exists()
