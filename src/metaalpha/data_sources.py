from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import time
from typing import Any, Callable

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


def normalize_akshare_index_frame(
    raw: pd.DataFrame,
    *,
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Normalize supported AKShare index-history outputs to the MetaAlpha contract.

    Supported providers expose either Chinese ``日期/开盘/...`` columns or
    already-normalized English ``date/open/...`` columns. Required schema and
    OHLC invariants are checked explicitly so provider fallback cannot silently
    mutate the research dataset contract.
    """
    if raw is None or raw.empty:
        raise ValueError("AKShare returned an empty index frame")

    out = raw.rename(columns={k: v for k, v in AKSHARE_INDEX_COLUMN_MAP.items() if k in raw.columns}).copy()
    required = {"date", "open", "close", "high", "low"}
    missing = required - set(out.columns)
    if missing:
        raise ValueError(f"AKShare index schema missing columns: {sorted(missing)}")

    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.normalize()
    if start_date is not None:
        out = out.loc[out["date"] >= pd.to_datetime(start_date, format="%Y%m%d")].copy()
    if end_date is not None:
        out = out.loc[out["date"] <= pd.to_datetime(end_date, format="%Y%m%d")].copy()
    if out.empty:
        raise ValueError("AKShare frame is empty after requested date filtering")

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


def _retry_call(
    fn: Callable[[], pd.DataFrame],
    *,
    retries: int,
    retry_sleep_seconds: float,
) -> pd.DataFrame:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            result = fn()
            if result is None or result.empty:
                raise ValueError("provider returned empty dataframe")
            return result
        except Exception as exc:  # pragma: no cover - upstream network behavior
            last_exc = exc
            if attempt + 1 < retries:
                time.sleep(retry_sleep_seconds * (attempt + 1))
    raise RuntimeError(f"provider failed after {retries} attempts") from last_exc


def fetch_akshare_index(
    *,
    symbol: str = "000001",
    start_date: str = "19901219",
    end_date: str = "22220101",
    retries: int = 2,
    retry_sleep_seconds: float = 1.5,
) -> tuple[pd.DataFrame, DataManifest]:
    """Fetch one A-share index through a deterministic AKShare provider chain.

    Provider order is frozen for this adapter version:

    1. ``stock_zh_index_daily_em`` — Eastmoney, direct market-qualified symbol;
    2. ``stock_zh_index_daily`` — Sina;
    3. ``stock_zh_index_daily_tx`` — Tencent;
    4. ``index_zh_a_hist`` — Eastmoney code-map interface, last resort.

    The first provider that returns a valid normalized frame wins. The actual
    provider is written to the manifest. This avoids making the statistical
    experiment depend on one brittle upstream discovery endpoint.
    """
    if retries < 1:
        raise ValueError("retries must be >= 1")

    try:
        import akshare as ak  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("AKShare is not installed; use `pip install -e '.[data]'`") from exc

    market_symbol = f"sh{symbol}"
    providers: list[tuple[str, str, Callable[[], pd.DataFrame]]] = [
        (
            "AKShare / Eastmoney direct index history",
            "ak.stock_zh_index_daily_em",
            lambda: ak.stock_zh_index_daily_em(
                symbol=market_symbol,
                start_date=start_date,
                end_date=end_date,
            ),
        ),
        (
            "AKShare / Sina index history",
            "ak.stock_zh_index_daily",
            lambda: ak.stock_zh_index_daily(symbol=market_symbol),
        ),
        (
            "AKShare / Tencent index history",
            "ak.stock_zh_index_daily_tx",
            lambda: ak.stock_zh_index_daily_tx(symbol=market_symbol),
        ),
        (
            "AKShare / Eastmoney mapped index history",
            "ak.index_zh_a_hist",
            lambda: ak.index_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
            ),
        ),
    ]

    errors: list[str] = []
    for source, method, call in providers:
        try:
            raw = _retry_call(
                call,
                retries=retries,
                retry_sleep_seconds=retry_sleep_seconds,
            )
            frame = normalize_akshare_index_frame(
                raw,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:  # pragma: no cover - upstream network behavior
            errors.append(f"{method}: {type(exc).__name__}: {exc}")
            continue

        manifest = DataManifest(
            source=source,
            source_method=method,
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

    detail = " | ".join(errors)
    raise RuntimeError(f"all AKShare index providers failed: {detail}")
