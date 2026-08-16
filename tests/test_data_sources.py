import pandas as pd
import pytest

from metaalpha.data_sources import canonical_frame_sha256, normalize_akshare_index_frame


def _raw_frame():
    return pd.DataFrame(
        {
            "日期": ["2024-01-03", "2024-01-02"],
            "开盘": [2960.0, 2950.0],
            "收盘": [2970.0, 2960.0],
            "最高": [2980.0, 2970.0],
            "最低": [2940.0, 2945.0],
            "成交量": [100, 90],
            "成交额": [1000.0, 900.0],
        }
    )


def test_normalize_akshare_index_frame_is_sorted_and_contract_safe():
    out = normalize_akshare_index_frame(_raw_frame(), symbol="000001")
    assert list(out["date"].dt.strftime("%Y-%m-%d")) == ["2024-01-02", "2024-01-03"]
    assert set(["symbol", "date", "open", "high", "low", "close"]).issubset(out.columns)
    assert out["symbol"].nunique() == 1
    assert out["symbol"].iloc[0] == "INDEX_000001"


def test_canonical_hash_is_stable_after_equivalent_normalization():
    a = normalize_akshare_index_frame(_raw_frame(), symbol="000001")
    b = normalize_akshare_index_frame(_raw_frame().iloc[::-1].reset_index(drop=True), symbol="000001")
    assert canonical_frame_sha256(a) == canonical_frame_sha256(b)


def test_invalid_ohlc_fails_loudly():
    raw = _raw_frame()
    raw.loc[0, "最高"] = 2900.0
    with pytest.raises(ValueError, match="invalid OHLC"):
        normalize_akshare_index_frame(raw, symbol="000001")
