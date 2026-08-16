from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .bazi_ziping import features_from_pillars
from .data_sources import DataManifest, fetch_akshare_index
from .ganzhi import pillars_from_datetime
from .labels import add_forward_labels

TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")

HYPOTHESIS_ID = "ZIPING_FWD_001"
VERSION = 1
FORWARD_START = pd.Timestamp("2026-08-17")
SESSION_ANCHOR_HOUR = 9
SESSION_ANCHOR_MINUTE = 25
FEATURE_NAME = "zpzt__v1__month_primary_ten_god"
FEATURE_LEVEL = "偏财"
TARGET = "ret_fwd_1"
PROVIDER = "sina"
SHIFT_NULLS = (17, 31, 47)
MIN_TOTAL_SESSIONS = 300
MIN_SIGNAL_SESSIONS = 30
MIN_EFFECT_BPS = 10.0
ONE_SIDED_ALPHA = 0.025
HAC_MAXLAGS = 5


@dataclass(frozen=True)
class ForwardGate:
    min_total_sessions: int = MIN_TOTAL_SESSIONS
    min_signal_sessions: int = MIN_SIGNAL_SESSIONS
    min_effect_bps: float = MIN_EFFECT_BPS
    one_sided_alpha: float = ONE_SIDED_ALPHA
    hac_maxlags: int = HAC_MAXLAGS


def _as_shanghai_datetime(value: datetime | str | pd.Timestamp) -> datetime:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize(TZ_SHANGHAI)
    else:
        ts = ts.tz_convert(TZ_SHANGHAI)
    return ts.to_pydatetime()


def _anchor_for_date(date_value: str | pd.Timestamp) -> datetime:
    d = pd.Timestamp(date_value).date()
    return datetime(
        d.year,
        d.month,
        d.day,
        SESSION_ANCHOR_HOUR,
        SESSION_ANCHOR_MINUTE,
        tzinfo=TZ_SHANGHAI,
    )


def generate_signal_record(
    date_value: str | pd.Timestamp,
    *,
    generated_at: datetime | str | pd.Timestamp | None = None,
) -> dict[str, object]:
    """Create one immutable, deterministic forward signal record.

    The record is valid for confirmatory scoring only when it was generated
    before the registered 09:25 Asia/Shanghai anchor and on/after 2026-08-17.
    A non-偏财 day is still recorded as a valid no-call observation; days are
    never cherry-picked after the outcome is known.
    """
    date = pd.Timestamp(date_value).normalize()
    generated = _as_shanghai_datetime(generated_at or datetime.now(timezone.utc))
    anchor = _anchor_for_date(date)

    pillars = pillars_from_datetime(
        date,
        anchor_hour=SESSION_ANCHOR_HOUR,
        anchor_minute=SESSION_ANCHOR_MINUTE,
    )
    features = features_from_pillars(pillars.year, pillars.month, pillars.day, pillars.time)
    feature_value = str(features[FEATURE_NAME])
    is_signal = feature_value == FEATURE_LEVEL

    active = date >= FORWARD_START
    precommitted = generated < anchor
    confirmatory_eligible = bool(active and precommitted)

    return {
        "schema_version": 1,
        "hypothesis_id": HYPOTHESIS_ID,
        "hypothesis_version": VERSION,
        "date": date.strftime("%Y-%m-%d"),
        "session_anchor": anchor.isoformat(),
        "generated_at": generated.isoformat(),
        "forward_start": FORWARD_START.strftime("%Y-%m-%d"),
        "feature": FEATURE_NAME,
        "registered_level": FEATURE_LEVEL,
        "feature_value": feature_value,
        "signal": int(is_signal),
        "forecast": "positive_next_session_return" if is_signal else "no_call",
        "active_after_registration": bool(active),
        "precommitted_before_anchor": bool(precommitted),
        "confirmatory_eligible": confirmatory_eligible,
        "calendar_status": "candidate_session_unconfirmed",
        "pillars": {
            "year": pillars.year,
            "month": pillars.month,
            "day": pillars.day,
            "time": pillars.time,
        },
        "method": "Ziping Zhenquan month-command-first operationalization",
        "provider_for_scoring": PROVIDER,
        "target": TARGET,
        "rule_hash_material": {
            "feature": FEATURE_NAME,
            "level": FEATURE_LEVEL,
            "target": TARGET,
            "anchor": "09:25 Asia/Shanghai",
            "start": "2026-08-17",
        },
    }


def write_signal_record(
    date_value: str | pd.Timestamp,
    out_path: Path,
    *,
    generated_at: datetime | str | pd.Timestamp | None = None,
) -> dict[str, object]:
    """Write a signal exactly once. Existing files are never overwritten."""
    if out_path.exists():
        raise FileExistsError(f"refusing to overwrite precommitted signal: {out_path}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    record = generate_signal_record(date_value, generated_at=generated_at)
    out_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return record


def load_signal_records(signals_dir: Path) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for path in sorted(signals_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("hypothesis_id") != HYPOTHESIS_ID:
            continue
        payload["source_file"] = str(path)
        records.append(payload)
    if not records:
        return pd.DataFrame()
    out = pd.DataFrame(records)
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.normalize()
    return out.sort_values("date").drop_duplicates("date", keep="first").reset_index(drop=True)


def _one_sided_positive_p(two_sided_p: float, coefficient: float) -> float:
    if not np.isfinite(two_sided_p):
        return float("nan")
    return float(two_sided_p / 2.0) if coefficient > 0 else float(1.0 - two_sided_p / 2.0)


def _fit_calendar_adjusted_hac(df: pd.DataFrame, signal_col: str) -> dict[str, float]:
    base = df[["date", TARGET, signal_col]].dropna().copy().sort_values("date")
    if base.empty or base[signal_col].nunique() < 2:
        return {
            "coefficient": float("nan"),
            "coefficient_bps": float("nan"),
            "p_two_sided": float("nan"),
            "p_one_sided_positive": float("nan"),
            "t_stat": float("nan"),
        }

    base["weekday"] = pd.to_datetime(base["date"]).dt.weekday.astype(str)
    base["month"] = pd.to_datetime(base["date"]).dt.month.astype(str)
    dummies = pd.get_dummies(base[["weekday", "month"]], drop_first=True, dtype=float)
    design = pd.concat(
        [base[[signal_col]].astype(float).reset_index(drop=True), dummies.reset_index(drop=True)],
        axis=1,
    )
    design = sm.add_constant(design, prepend=True)
    fitted = sm.OLS(base[TARGET].to_numpy(dtype=float), design).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": HAC_MAXLAGS, "use_correction": True},
    )
    coefficient = float(fitted.params[signal_col])
    p_two = float(fitted.pvalues[signal_col])
    return {
        "coefficient": coefficient,
        "coefficient_bps": coefficient * 10000.0,
        "p_two_sided": p_two,
        "p_one_sided_positive": _one_sided_positive_p(p_two, coefficient),
        "t_stat": float(fitted.tvalues[signal_col]),
    }


def _half_mean_differences(df: pd.DataFrame) -> tuple[float, float]:
    ordered = df.sort_values("date").reset_index(drop=True)
    midpoint = len(ordered) // 2
    values: list[float] = []
    for part in (ordered.iloc[:midpoint], ordered.iloc[midpoint:]):
        signal = part.loc[part["signal"] == 1, TARGET]
        rest = part.loc[part["signal"] == 0, TARGET]
        if signal.empty or rest.empty:
            values.append(float("nan"))
        else:
            values.append(float(signal.mean() - rest.mean()))
    return values[0], values[1]


def score_forward_experiment(
    market: pd.DataFrame,
    signals: pd.DataFrame,
    *,
    gate: ForwardGate = ForwardGate(),
) -> dict[str, object]:
    """Score only immutable, pre-anchor forward records against realized data."""
    if signals.empty:
        return {
            "hypothesis_id": HYPOTHESIS_ID,
            "status": "COLLECTING",
            "reason": "no signal records",
            "total_scored_sessions": 0,
            "signal_sessions": 0,
        }

    required_signal_cols = {"date", "signal", "confirmatory_eligible"}
    missing = required_signal_cols - set(signals.columns)
    if missing:
        raise ValueError(f"signal records missing columns: {sorted(missing)}")
    if not {"date", "close"}.issubset(market.columns):
        raise ValueError("market data requires date and close")

    m = market.copy()
    if "symbol" not in m.columns:
        m["symbol"] = "INDEX_000001"
    m["date"] = pd.to_datetime(m["date"], errors="raise").dt.normalize()
    m = add_forward_labels(m, horizons=(1,))

    s = signals.copy()
    s["date"] = pd.to_datetime(s["date"], errors="raise").dt.normalize()
    s = s.loc[s["confirmatory_eligible"].astype(bool)].copy()

    joined = m[["date", "close", TARGET]].merge(
        s[["date", "signal"]], on="date", how="inner", validate="one_to_one"
    )
    joined = joined.dropna(subset=[TARGET]).sort_values("date").reset_index(drop=True)

    if joined.empty:
        return {
            "hypothesis_id": HYPOTHESIS_ID,
            "status": "COLLECTING",
            "reason": "no realized next-session outcomes yet",
            "total_scored_sessions": 0,
            "signal_sessions": 0,
        }

    joined["signal"] = joined["signal"].astype(int)
    for shift in SHIFT_NULLS:
        joined[f"shift_{shift}"] = joined["signal"].shift(shift)

    signal_returns = joined.loc[joined["signal"] == 1, TARGET]
    non_signal_returns = joined.loc[joined["signal"] == 0, TARGET]
    raw_diff = (
        float(signal_returns.mean() - non_signal_returns.mean())
        if not signal_returns.empty and not non_signal_returns.empty
        else float("nan")
    )

    primary = _fit_calendar_adjusted_hac(joined, "signal")
    null_models: dict[str, dict[str, float]] = {}
    for shift in SHIFT_NULLS:
        col = f"shift_{shift}"
        null_models[str(shift)] = _fit_calendar_adjusted_hac(joined.dropna(subset=[col]), col)

    finite_null_betas = [
        x["coefficient_bps"]
        for x in null_models.values()
        if np.isfinite(x["coefficient_bps"])
    ]
    max_null_beta_bps = max(finite_null_betas) if finite_null_betas else float("nan")
    first_half_diff, second_half_diff = _half_mean_differences(joined)

    total = int(len(joined))
    signal_n = int((joined["signal"] == 1).sum())
    sample_ready = total >= gate.min_total_sessions and signal_n >= gate.min_signal_sessions

    checks = {
        "sample_ready": sample_ready,
        "positive_calendar_adjusted_effect": bool(primary["coefficient_bps"] > 0),
        "minimum_effect_met": bool(primary["coefficient_bps"] >= gate.min_effect_bps),
        "one_sided_alpha_met": bool(primary["p_one_sided_positive"] <= gate.one_sided_alpha),
        "first_half_positive": bool(np.isfinite(first_half_diff) and first_half_diff > 0),
        "second_half_positive": bool(np.isfinite(second_half_diff) and second_half_diff > 0),
        "beats_shift_nulls": bool(
            np.isfinite(max_null_beta_bps)
            and primary["coefficient_bps"] > max_null_beta_bps
        ),
    }
    confirmed = sample_ready and all(v for k, v in checks.items() if k != "sample_ready")
    status = "CONFIRMED_FORWARD_CANDIDATE" if confirmed else ("GATE_FAILED" if sample_ready else "COLLECTING")

    return {
        "schema_version": 1,
        "hypothesis_id": HYPOTHESIS_ID,
        "hypothesis_version": VERSION,
        "status": status,
        "provider": PROVIDER,
        "target": TARGET,
        "total_scored_sessions": total,
        "signal_sessions": signal_n,
        "non_signal_sessions": int((joined["signal"] == 0).sum()),
        "first_scored_date": joined["date"].min().strftime("%Y-%m-%d"),
        "last_scored_date": joined["date"].max().strftime("%Y-%m-%d"),
        "signal_mean_return": float(signal_returns.mean()) if not signal_returns.empty else float("nan"),
        "non_signal_mean_return": float(non_signal_returns.mean()) if not non_signal_returns.empty else float("nan"),
        "raw_mean_difference": raw_diff,
        "raw_mean_difference_bps": raw_diff * 10000.0 if np.isfinite(raw_diff) else float("nan"),
        "calendar_adjusted_hac": primary,
        "shift_null_hac": null_models,
        "max_shift_null_beta_bps": max_null_beta_bps,
        "first_half_raw_difference_bps": first_half_diff * 10000.0 if np.isfinite(first_half_diff) else float("nan"),
        "second_half_raw_difference_bps": second_half_diff * 10000.0 if np.isfinite(second_half_diff) else float("nan"),
        "gate": {
            "min_total_sessions": gate.min_total_sessions,
            "min_signal_sessions": gate.min_signal_sessions,
            "min_effect_bps": gate.min_effect_bps,
            "one_sided_alpha": gate.one_sided_alpha,
            "hac_maxlags": gate.hac_maxlags,
        },
        "checks": checks,
        "rule": f"{FEATURE_NAME} == {FEATURE_LEVEL} predicts positive {TARGET}",
    }


def write_score_outputs(
    market: pd.DataFrame,
    signals_dir: Path,
    out_dir: Path,
    *,
    manifest: DataManifest | None = None,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    signals = load_signal_records(signals_dir)
    result = score_forward_experiment(market, signals)
    (out_dir / "latest_status.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=True) + "\n",
        encoding="utf-8",
    )
    if manifest is not None:
        (out_dir / "latest_data_manifest.json").write_text(manifest.to_json() + "\n", encoding="utf-8")

    gate_path = out_dir / "gate_result.json"
    if result.get("status") in {"CONFIRMED_FORWARD_CANDIDATE", "GATE_FAILED"} and not gate_path.exists():
        gate_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=True) + "\n",
            encoding="utf-8",
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Forward-only Ziping Zhenquan experiment tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    p_signal = sub.add_parser("signal", help="create one immutable pre-outcome signal")
    p_signal.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_signal.add_argument("--out", type=Path, required=True)

    p_score = sub.add_parser("score", help="score all eligible signals with pinned Sina data")
    p_score.add_argument("--signals-dir", type=Path, required=True)
    p_score.add_argument("--out-dir", type=Path, required=True)
    p_score.add_argument("--symbol", default="000001")
    p_score.add_argument("--start", default="20260817")
    p_score.add_argument("--end", required=True)
    p_score.add_argument("--provider", default=PROVIDER, choices=(PROVIDER,))

    args = parser.parse_args()
    if args.command == "signal":
        record = write_signal_record(args.date, args.out)
        print(json.dumps(record, ensure_ascii=False, sort_keys=True))
        return

    market, manifest = fetch_akshare_index(
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end,
        provider=args.provider,
    )
    result = write_score_outputs(market, args.signals_dir, args.out_dir, manifest=manifest)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=True))


if __name__ == "__main__":
    main()
