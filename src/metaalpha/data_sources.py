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

PROVIDER_ORDER = (
    "eastmoney_direct",
    "sina",
    "tencent",
    "eastmoney_mapped",
)


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
            "open", "high", "low", "close", "volume", "amount",
            "amplitude_pct", "change_pct", "change", "turnover_pct",
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
            "symbol", "date", "open", "high", "low", "close", "volume", "amount",
            "amplitude_pct", "change_pct", "change", "turnover_pct",
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


def _split_market_symbol(symbol: str) -> tuple[str, str, str]:
    """Return (market_prefix, bare_code, provider_symbol).

    Existing bare-code calls remain Shanghai by default for backward
    compatibility. Replication work can pass explicit ``sz399001`` etc.
    """
    s = str(symbol).strip().lower()
    if s.startswith(("sh", "sz")):
        prefix = s[:2]
        bare = s[2:]
    else:
        prefix = "sh"
        bare = s
    if prefix not in {"sh", "sz"} or not bare.isdigit() or len(bare) != 6:
        raise ValueError("index symbol must be a 6-digit code or explicit sh/sz + 6-digit code")
    return prefix, bare, f"{prefix}{bare}"


def _provider_definitions(ak, *, symbol: str, start_date: str, end_date: str):
    _, bare_symbol, market_symbol = _split_market_symbol(symbol)
    return {
        "eastmoney_direct": (
            "AKShare / Eastmoney direct index history",
            "ak.stock_zh_index_daily_em",
            lambda: ak.stock_zh_index_daily_em(
                symbol=market_symbol,
                start_date=start_date,
                end_date=end_date,
            ),
        ),
        "sina": (
            "AKShare / Sina index history",
            "ak.stock_zh_index_daily",
            lambda: ak.stock_zh_index_daily(symbol=market_symbol),
        ),
        "tencent": (
            "AKShare / Tencent index history",
            "ak.stock_zh_index_daily_tx",
            lambda: ak.stock_zh_index_daily_tx(symbol=market_symbol),
        ),
        "eastmoney_mapped": (
            "AKShare / Eastmoney mapped index history",
            "ak.index_zh_a_hist",
            lambda: ak.index_zh_a_hist(
                symbol=bare_symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
            ),
        ),
    }


def fetch_akshare_index(
    *,
    symbol: str = "000001",
    start_date: str = "19901219",
    end_date: str = "22220101",
    provider: str = "auto",
    retries: int = 2,
    retry_sleep_seconds: float = 1.5,
) -> tuple[pd.DataFrame, DataManifest]:
    """Fetch one A-share index with either a pinned provider or frozen fallback chain.

    ``symbol`` accepts either a legacy bare six-digit code (treated as Shanghai,
    preserving existing behavior) or an explicit provider-style code such as
    ``sz399001``. ``provider='auto'`` is suitable for availability but not for
    strict cross-run numerical comparison. Confirmatory research must pin a
    provider explicitly and record its manifest/hash.
    """
    if retries < 1:
        raise ValueError("retries must be >= 1")
    if provider != "auto" and provider not in PROVIDER_ORDER:
        raise ValueError(f"unknown provider {provider!r}; expected auto or one of {PROVIDER_ORDER}")
    _split_market_symbol(symbol)

    try:
        import akshare as ak  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("AKShare is not installed; use `pip install -e '.[data]'`") from exc

    providers = _provider_definitions(ak, symbol=symbol, start_date=start_date, end_date=end_date)
    selected = PROVIDER_ORDER if provider == "auto" else (provider,)

    errors: list[str] = []
    for provider_key in selected:
        source, method, call = providers[provider_key]
        try:
            raw = _retry_call(call, retries=retries, retry_sleep_seconds=retry_sleep_seconds)
            frame = normalize_akshare_index_frame(
                raw,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:  # pragma: no cover - upstream network behavior
            errors.append(f"{provider_key}/{method}: {type(exc).__name__}: {exc}")
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
    if provider == "auto":
        raise RuntimeError(f"all AKShare index providers failed: {detail}")
    raise RuntimeError(f"pinned provider {provider!r} failed; no fallback allowed: {detail}")
