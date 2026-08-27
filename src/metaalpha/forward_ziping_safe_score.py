from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from . import forward_ziping as core
from .data_sources import DataManifest, fetch_akshare_index


_ORIGINAL_HAC = core._fit_calendar_adjusted_hac
_ORIGINAL_SCORE = core.score_forward_experiment


def _nan_hac() -> dict[str, float]:
    return {
        "coefficient": float("nan"),
        "coefficient_bps": float("nan"),
        "p_two_sided": float("nan"),
        "p_one_sided_positive": float("nan"),
        "t_stat": float("nan"),
    }


def _guarded_hac(
    df: pd.DataFrame,
    signal_col: str,
    *,
    maxlags: int,
) -> dict[str, float]:
    """Return an unestimated HAC result when the tiny sample is saturated.

    ZIPING_FWD_001 starts with only a handful of forward observations. Calendar
    dummies can make nobs <= k_params, where statsmodels' finite-sample HAC
    correction divides by nobs-k_params and raises ZeroDivisionError. That is
    not research evidence and must not make the daily collection workflow fail.

    Once the design has positive residual degrees of freedom, delegate to the
    frozen scoring implementation unchanged.
    """
    base = df[["date", core.TARGET, signal_col]].dropna().copy().sort_values("date")
    if base.empty or base[signal_col].nunique() < 2:
        return _nan_hac()

    base["weekday"] = pd.to_datetime(base["date"]).dt.weekday.astype(str)
    base["month"] = pd.to_datetime(base["date"]).dt.month.astype(str)
    dummies = pd.get_dummies(base[["weekday", "month"]], drop_first=True, dtype=float)
    design = pd.concat(
        [base[[signal_col]].astype(float).reset_index(drop=True), dummies.reset_index(drop=True)],
        axis=1,
    )
    design = sm.add_constant(design, prepend=True)

    if len(base) <= int(design.shape[1]):
        return _nan_hac()

    try:
        return _ORIGINAL_HAC(df, signal_col, maxlags=maxlags)
    except ZeroDivisionError:
        # Belt-and-suspenders protection against future statsmodels changes.
        return _nan_hac()


def _suppress_inference_until_gate(result: dict[str, object]) -> dict[str, object]:
    checks = result.get("checks")
    if not isinstance(checks, dict) or bool(checks.get("sample_ready")):
        return result

    result = dict(result)
    result["calendar_adjusted_hac"] = _nan_hac()
    result["shift_null_hac"] = {str(shift): _nan_hac() for shift in core.SHIFT_NULLS}
    result["max_shift_null_beta_bps"] = float("nan")
    result["reason"] = (
        "inferential HAC statistics suppressed until the frozen total/signal sample gate is reached"
    )
    return result


def score_forward_experiment(
    market: pd.DataFrame,
    signals: pd.DataFrame,
    *,
    gate: core.ForwardGate = core.ForwardGate(),
) -> dict[str, object]:
    original_hac = core._fit_calendar_adjusted_hac
    core._fit_calendar_adjusted_hac = _guarded_hac
    try:
        result = _ORIGINAL_SCORE(market, signals, gate=gate)
    finally:
        core._fit_calendar_adjusted_hac = original_hac
    return _suppress_inference_until_gate(result)


def write_score_outputs(
    market: pd.DataFrame,
    signals_dir: Path,
    out_dir: Path,
    *,
    manifest: DataManifest | None = None,
) -> dict[str, object]:
    original_hac = core._fit_calendar_adjusted_hac
    original_score = core.score_forward_experiment
    core._fit_calendar_adjusted_hac = _guarded_hac
    core.score_forward_experiment = score_forward_experiment
    try:
        return core.write_score_outputs(market, signals_dir, out_dir, manifest=manifest)
    finally:
        core._fit_calendar_adjusted_hac = original_hac
        core.score_forward_experiment = original_score


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Production-safe ZIPING_FWD_001 scorer with tiny-sample HAC guard"
    )
    parser.add_argument("--signals-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--start", default="20260817")
    parser.add_argument("--end", required=True)
    parser.add_argument("--provider", default=core.PROVIDER, choices=(core.PROVIDER,))
    args = parser.parse_args()

    market, manifest = fetch_akshare_index(
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end,
        provider=args.provider,
    )
    result = write_score_outputs(
        market,
        args.signals_dir,
        args.out_dir,
        manifest=manifest,
    )
    print(json.dumps(core._json_safe(result), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
