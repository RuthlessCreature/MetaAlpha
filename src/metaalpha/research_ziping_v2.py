from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .controls import add_shifted_feature
from .data_sources import DataManifest, fetch_akshare_index
from .pipeline import build_dataset
from .validation import evaluate_categorical_family


HYPOTHESIS_ID = "ZIPING_V2_001"
FEATURES = (
    "zpzt_use__v2__selected_ten_god",
    "zpzt_use__v2__selected_pattern_candidate",
    "zpzt_use__v2__selection_mode",
    "zpzt_use__v2__use_change_detected",
    "zpzt_use__v2__composition_mode",
    "zpzt_use__v2__mixed_families",
    "zpzt_use__v2__harmony_family",
    "zpzt_use__v2__transmitted_count",
)
TARGET = "ret_fwd_1"
SHIFT_SESSIONS = (17, 31, 47)
HAC_MAXLAGS = 5
MIN_N = 100

ERAS = (
    ("history_all", None, "2026-08-14"),
    ("era_1990_2004", None, "2004-12-31"),
    ("era_2005_2014", "2005-01-01", "2014-12-31"),
    ("era_2015_2020", "2015-01-01", "2020-12-31"),
    ("era_2021_2026", "2021-01-01", "2026-08-14"),
)

CALENDAR_BASELINE = ("calendar__v1__weekday", "calendar__v1__month")


@dataclass(frozen=True)
class EraResult:
    era: str
    start: str | None
    end: str | None
    rows_before_purge: int
    rows_after_purge: int


def _slice_and_purge(
    df: pd.DataFrame,
    *,
    start: str | None,
    end: str | None,
    horizon: int = 1,
) -> tuple[pd.DataFrame, EraResult]:
    dates = pd.to_datetime(df["date"], errors="raise")
    mask = pd.Series(True, index=df.index)
    if start is not None:
        mask &= dates >= pd.Timestamp(start)
    if end is not None:
        mask &= dates <= pd.Timestamp(end)
    part = df.loc[mask].copy().sort_values("date").reset_index(drop=True)
    before = len(part)
    if horizon > 0 and len(part) > horizon:
        part = part.iloc[:-horizon].copy()
    elif horizon > 0:
        part = part.iloc[:0].copy()
    return part, EraResult("", start, end, before, len(part))


def _add_shift_nulls(df: pd.DataFrame) -> tuple[pd.DataFrame, tuple[str, ...]]:
    out = df.copy()
    names: list[str] = []
    for feature in FEATURES:
        for shift in SHIFT_SESSIONS:
            out = add_shifted_feature(out, feature, shift_rows=shift)
            names.append(f"control__v1__shift_{shift}__{feature}")
    return out, tuple(names)


def _evaluate_family(
    df: pd.DataFrame,
    features: tuple[str, ...],
    *,
    family_name: str,
    test_kind: str,
    era: str,
    min_n: int,
) -> pd.DataFrame:
    result = evaluate_categorical_family(
        df,
        features,
        TARGET,
        family_name=family_name,
        min_n=min_n,
        inference="hac",
        hac_maxlags=HAC_MAXLAGS,
    )
    if result.empty:
        return result
    result.insert(0, "hypothesis_id", HYPOTHESIS_ID)
    result.insert(1, "era", era)
    result.insert(2, "test_kind", test_kind)
    return result


def _diagnostic_summary(screen: pd.DataFrame) -> pd.DataFrame:
    if screen.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for keys, group in screen.groupby(["era", "test_kind"], dropna=False):
        rows.append(
            {
                "era": keys[0],
                "test_kind": keys[1],
                "tests": int(len(group)),
                "min_family_fdr": float(group["p_fdr_bh_family"].min()),
                "max_abs_effect_std": float(group["effect_std"].abs().max()),
                "median_abs_effect_std": float(group["effect_std"].abs().median()),
            }
        )
    return pd.DataFrame(rows).sort_values(["era", "test_kind"]).reset_index(drop=True)


def _directional_stability(screen: pd.DataFrame) -> pd.DataFrame:
    if screen.empty:
        return pd.DataFrame()
    registered = screen.loc[
        (screen["test_kind"] == "registered") & (screen["era"] != "history_all")
    ].copy()
    if registered.empty:
        return pd.DataFrame()

    registered["level_key"] = registered["level"].astype(str)
    rows: list[dict[str, object]] = []
    for (feature, level_key), group in registered.groupby(["feature", "level_key"], dropna=False):
        effects = group["effect_std"].astype(float)
        positive = int((effects > 0).sum())
        negative = int((effects < 0).sum())
        rows.append(
            {
                "feature": feature,
                "level": level_key,
                "eras_present": int(group["era"].nunique()),
                "positive_eras": positive,
                "negative_eras": negative,
                "same_sign_eras": max(positive, negative),
                "median_effect_std": float(effects.median()),
                "min_family_fdr_across_eras": float(group["p_fdr_bh_family"].min()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["same_sign_eras", "min_family_fdr_across_eras", "feature"],
        ascending=[False, True, True],
    ).reset_index(drop=True)


def run_ziping_v2_exploration(
    raw: pd.DataFrame,
    *,
    out_dir: Path,
    manifest: DataManifest | None = None,
    min_n: int = MIN_N,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    dataset = build_dataset(raw, include_ziping=True)
    dataset.to_csv(out_dir / "dataset_ziping_v2.csv", index=False)

    screens: list[pd.DataFrame] = []
    era_rows: list[dict[str, object]] = []

    for era_name, start, end in ERAS:
        part, info = _slice_and_purge(dataset, start=start, end=end, horizon=1)
        era_rows.append(
            {
                "era": era_name,
                "start": start or pd.to_datetime(part["date"]).min().strftime("%Y-%m-%d") if not part.empty else start,
                "end": end or pd.to_datetime(part["date"]).max().strftime("%Y-%m-%d") if not part.empty else end,
                "rows_before_purge": info.rows_before_purge,
                "rows_after_purge": info.rows_after_purge,
            }
        )
        if part.empty:
            continue

        registered = _evaluate_family(
            part,
            FEATURES,
            family_name="ziping_use_change_v2",
            test_kind="registered",
            era=era_name,
            min_n=min_n,
        )
        if not registered.empty:
            screens.append(registered)

        shifted, null_features = _add_shift_nulls(part)
        null = _evaluate_family(
            shifted,
            null_features,
            family_name="ziping_use_change_v2__shift_null",
            test_kind="shift_null",
            era=era_name,
            min_n=min_n,
        )
        if not null.empty:
            screens.append(null)

        baseline = _evaluate_family(
            part,
            CALENDAR_BASELINE,
            family_name="gregorian_baseline_v1",
            test_kind="calendar_baseline",
            era=era_name,
            min_n=min_n,
        )
        if not baseline.empty:
            screens.append(baseline)

    screen = pd.concat(screens, ignore_index=True) if screens else pd.DataFrame()
    diagnostics = _diagnostic_summary(screen)
    stability = _directional_stability(screen)
    era_table = pd.DataFrame(era_rows)

    screen.to_csv(out_dir / "historical_exploratory_screen.csv", index=False)
    diagnostics.to_csv(out_dir / "diagnostic_summary.csv", index=False)
    stability.to_csv(out_dir / "directional_stability.csv", index=False)
    era_table.to_csv(out_dir / "era_boundaries.csv", index=False)

    if manifest is not None:
        (out_dir / "data_manifest.json").write_text(manifest.to_json() + "\n", encoding="utf-8")

    metadata = {
        "hypothesis_id": HYPOTHESIS_ID,
        "status": "EXPLORATORY_ONLY_NO_UNSEEN_HISTORY",
        "historical_last_date": "2026-08-14",
        "provider_required": "sina",
        "features": list(FEATURES),
        "target": TARGET,
        "shift_null_sessions": list(SHIFT_SESSIONS),
        "hac_maxlags": HAC_MAXLAGS,
        "minimum_observations_per_level": min_n,
        "target_horizon_purge_sessions": 1,
        "rows": int(len(dataset)),
        "aggregate_fortune_score_defined": False,
    }
    (out_dir / "run_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# ZIPING_V2_001 — Month-Use Change Historical Exploration",
        "",
        "**Evidence status: EXPLORATORY ONLY. No historical observation is an unseen holdout.**",
        "",
        "This family tests source-constrained 月令藏干透出 / 用神变化 / 会支 primitives. It defines no numerical fortune score.",
        "",
        "## Data and inference",
        "",
        f"- rows: {len(dataset)}",
        "- canonical provider: pinned Sina",
        f"- target: `{TARGET}`",
        f"- HAC maxlags: {HAC_MAXLAGS}",
        "- BH-FDR is applied across the complete registered feature family within each era/test class.",
        "- Each era purges its final session so next-session return cannot cross the descriptive era boundary.",
        "",
        "## Diagnostic minima",
        "",
    ]
    if diagnostics.empty:
        lines.append("No eligible tests met the minimum sample threshold.")
    else:
        lines.append(diagnostics.to_markdown(index=False))
    lines.extend(
        [
            "",
            "## Interpretation gate",
            "",
            "A low historical FDR is nomination-only. A v2 state is interesting only if its sign is stable across later eras and it is not materially weaker than shifted-session controls. Any actual confirmation requires a separately frozen future-only hypothesis.",
        ]
    )
    (out_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "dataset": dataset,
        "screen": screen,
        "diagnostics": diagnostics,
        "stability": stability,
        "eras": era_table,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ZIPING_V2_001 historical exploration")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--fetch-akshare", action="store_true")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--start", default="19901219")
    parser.add_argument("--end", default="20260814")
    parser.add_argument("--provider", default="sina", choices=("sina",))
    parser.add_argument("--out", type=Path, default=Path("reports/sse_ziping_v2_exploratory"))
    parser.add_argument("--min-n", type=int, default=MIN_N)
    args = parser.parse_args()

    manifest: DataManifest | None = None
    if args.fetch_akshare:
        raw, manifest = fetch_akshare_index(
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
            provider=args.provider,
        )
    else:
        raw = pd.read_csv(args.input)

    result = run_ziping_v2_exploration(raw, out_dir=args.out, manifest=manifest, min_n=args.min_n)
    print(f"rows={len(result['dataset'])}")
    print(f"screen_tests={len(result['screen'])}")
    print(f"report={args.out / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
