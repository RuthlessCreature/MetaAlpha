from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import time
from typing import Any

import pandas as pd


AKSHARE_INDEX_COLUMN_MAP = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude_pct",
    "涨跌幅": "change_pct",
    "涨跌额": "change",
    "换手率": "turnover_pct",
}


@dataclass(frozen=True)
class DataManifest:
    source: str
    source_method: str
    source_version: str
    symbol: str
    requested_start: str
    requested_end: str
    fetched_at_utc: str
    rows: int
    first_date: str
    last_date: str
    canonical_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)


def canonical_frame_sha256(df: pd.DataFrame) -> str:
    """Hash a normalized market frame in a stable, machine-reproducible form."""
    cols = [c for c in ("symbol", "date", "open", "high", "low", "close", "volume", "amount") if c in df.columns]
    x = df[cols].copy()
    if "date" in x.columns:
        x["date"] = pd.to_datetime(x["date"], errors="raise").dt.strftime("%Y-%m-%d")
    payload = x.to_csv(index=False, lineterminator="\n", float_format="%.10g").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalize_akshare_index_frame(raw: pd.DataFrame, *, symbol: str) -> pd.DataFrame:
    """Normalize AKShare ``index_zh_a_hist`` output to the MetaAlpha OHLCV contract.

    This function deliberately validates the upstream schema instead of silently
    accepting changed column names. An upstream interface mutation must fail
    loudly so a different dataset is never mistaken for the registered one.
    """
    if raw is None or raw.empty:
        raise ValueError("AKShare returned an empty index frame")

    required_cn = {"日期", "开盘", "收盘", "最高", "最低"}
    missing = required_cn - set(raw.columns)
    if missing:
        raise ValueError(f"AKShare index schema missing columns: {sorted(missing)}")

    out = raw.rename(columns={k: v for k, v in AKSHARE_INDEX_COLUMN_MAP.items() if k in raw.columns}).copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.normalize()

    numeric_cols = [
        c
        for c in (
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
            "amplitude_pct",
            "change_pct",
            "change",
            "turnover_pct",
        )
        if c in out.columns
    ]
    for c in numeric_cols:
        out[c] = pd.to_numeric(out[c], errors="raise")

    out["symbol"] = f"INDEX_{symbol}"
    out = out.sort_values("date").drop_duplicates(subset=["symbol", "date"], keep="last").reset_index(drop=True)

    if (out[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("non-positive index OHLC value detected")
    invalid_high = out["high"] < out[["open", "close", "low"]].max(axis=1)
    invalid_low = out["low"] > out[["open", "close", "high"]].min(axis=1)
    if invalid_high.any() or invalid_low.any():
        raise ValueError("invalid OHLC ordering detected in upstream index data")

    preferred = [
        c
        for c in (
            "symbol",
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
            "amplitude_pct",
            "change_pct",
            "change",
            "turnover_pct",
        )
        if c in out.columns
    ]
    return out[preferred]


def fetch_akshare_index(
    *,
    symbol: str = "000001",
    start_date: str = "19901219",
    end_date: str = "22220101",
    retries: int = 3,
    retry_sleep_seconds: float = 2.0,
) -> tuple[pd.DataFrame, DataManifest]:
    """Fetch one A-share index with AKShare and return normalized data + provenance.

    AKShare is imported lazily so the core research package does not require the
    network/data dependency. The dependency is pinned in the ``data`` extra.
    """
    if retries < 1:
        raise ValueError("retries must be >= 1")

    try:
        import akshare as ak  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("AKShare is not installed; use `pip install -e '.[data]'`") from exc

    last_exc: Exception | None = None
    raw: pd.DataFrame | None = None
    for attempt in range(retries):
        try:
            raw = ak.index_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
            )
            break
        except Exception as exc:  # pragma: no cover - upstream network behavior
            last_exc = exc
            if attempt + 1 < retries:
                time.sleep(retry_sleep_seconds * (attempt + 1))

    if raw is None:
        raise RuntimeError(f"AKShare index_zh_a_hist failed after {retries} attempts") from last_exc

    frame = normalize_akshare_index_frame(raw, symbol=symbol)
    if frame.empty:
        raise RuntimeError("normalized AKShare index frame is empty")

    manifest = DataManifest(
        source="AKShare / Eastmoney upstream",
        source_method="ak.index_zh_a_hist",
        source_version=str(getattr(ak, "__version__", "unknown")),
        symbol=symbol,
        requested_start=start_date,
        requested_end=end_date,
        fetched_at_utc=datetime.now(timezone.utc).isoformat(),
        rows=int(len(frame)),
        first_date=frame["date"].min().strftime("%Y-%m-%d"),
        last_date=frame["date"].max().strftime("%Y-%m-%d"),
        canonical_sha256=canonical_frame_sha256(frame),
    )
    return frame, manifest
