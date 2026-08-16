from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import timedelta
import json
from pathlib import Path
from typing import Iterable

import pandas as pd

from .controls import add_shifted_feature
from .data_sources import DataManifest, fetch_akshare_index
from .labels import add_forward_labels
from .natal_transit import (
    NatalChartSpec,
    SSE_NATAL_V1,
    add_sse_natal_transit_features,
    features_for_transit_datetime,
)
from .validation import evaluate_categorical_family


@dataclass(frozen=True)
class NatalExperimentSpec:
    hypothesis_id: str
    target: str
    features: tuple[str, ...]
    family_name: str


EXPERIMENTS: tuple[NatalExperimentSpec, ...] = (
    NatalExperimentSpec(
        hypothesis_id="SSE_NATAL_001",
        target="ret_fwd_1",
        family_name="sse_natal_daily_return_v1",
        features=(
            "natal_transit__v1__day_stem_ten_god",
            "natal_transit__v1__day_branch_primary_ten_god",
            "natal_transit__v1__day_clashes_natal_day",
            "natal_transit__v1__day_clashes_natal_month",
            "natal_transit__v1__day_harms_natal_day",
            "natal_transit__v1__day_harms_natal_month",
            "natal_transit__v1__day_breaks_natal_day",
            "natal_transit__v1__day_breaks_natal_month",
            "natal_transit__v1__day_six_combines_natal_day",
            "natal_transit__v1__day_six_combines_natal_month",
            "natal_transit__v1__disruption_relation_count",
        ),
    ),
    NatalExperimentSpec(
        hypothesis_id="SSE_NATAL_002",
        target="vol_fwd_5",
        family_name="sse_natal_risk_v1",
        features=(
            "natal_transit__v1__branch_clash_count",
            "natal_transit__v1__branch_harm_count",
            "natal_transit__v1__branch_break_count",
            "natal_transit__v1__branch_six_combine_count",
            "natal_transit__v1__disruption_relation_count",
            "natal_transit__v1__month_branch_clashes_natal_count",
            "natal_transit__v1__month_branch_harms_natal_count",
            "natal_transit__v1__month_branch_breaks_natal_count",
            "natal_transit__v1__day_branch_clashes_natal_count",
            "natal_transit__v1__day_branch_harms_natal_count",
            "natal_transit__v1__day_branch_breaks_natal_count",
        ),
    ),
)

SHIFT_SESSIONS = (17, 31, 47)
FAKE_NATAL_OFFSETS = (17, 31, 47)

# These are descriptive historical eras only. None is a holdout.
ERAS = (
    ("history_all", None, "2026-08-14"),
    ("era_1990_2004", None, "2004-12-31"),
    ("era_2005_2014", "2005-01-01", "2014-12-31"),
    ("era_2015_2020", "2015-01-01", "2020-12-31"),
    ("era_2021_2026", "2021-01-01", "2026-08-14"),
)


def fake_natal_specs() -> tuple[NatalChartSpec, ...]:
    return tuple(
        NatalChartSpec(
            id=f"SSE_FAKE_NATAL_P{offset}",
            anchor=SSE_NATAL_V1.anchor + timedelta(days=offset),
            source="deterministic fake-anchor control",
            rationale=f"SSE_NATAL_V1 plus {offset} calendar days; control only",
        )
        for offset in FAKE_NATAL_OFFSETS
    )


def _slice_dates(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    dates = pd.to_datetime(df["date"], errors="raise")
    mask = pd.Series(True, index=df.index)
    if start is not None:
        mask &= dates >= pd.Timestamp(start)
    if end is not None:
        mask &= dates <= pd.Timestamp(end)
    return df.loc[mask].copy()


def _fake_feature_name(spec_id: str, real_feature: str) -> str:
    suffix = real_feature.removeprefix("natal_transit__v1__")
    return f"control_fake_natal__{spec_id}__{suffix}"


def _all_registered_features() -> tuple[str, ...]:
    return tuple(sorted({feature for spec in EXPERIMENTS for feature in spec.features}))


def _add_fake_natal_features_once(
    df: pd.DataFrame,
    *,
    real_features: Iterable[str],
) -> pd.DataFrame:
    """Calculate each fake natal chart once for the full dataset.

    Earlier prototype code recalculated the same fake chart for each era and
    hypothesis. That was statistically equivalent but wasteful. This version
    changes only execution cost, not any registered feature definition.
    """
    out = df.copy()
    dates = out["date"].tolist()
    wanted = tuple(real_features)
    new_columns: dict[str, pd.Series] = {}

    for spec in fake_natal_specs():
        rows = [features_for_transit_datetime(v, spec=spec) for v in dates]
        feat = pd.DataFrame(rows, index=out.index)
        for real_feature in wanted:
            if real_feature not in feat.columns:
                raise ValueError(f"fake natal engine missing registered feature: {real_feature}")
            new_columns[_fake_feature_name(spec.id, real_feature)] = feat[real_feature]

    if new_columns:
        out = pd.concat([out, pd.DataFrame(new_columns, index=out.index)], axis=1)
    return out


def _add_shift_nulls_once(
    df: pd.DataFrame,
    *,
    real_features: Iterable[str],
) -> pd.DataFrame:
    out = df.copy()
    for feature in real_features:
        for shift in SHIFT_SESSIONS:
            out = add_shifted_feature(out, feature, shift_rows=shift)
    return out


def _shift_features_for(spec: NatalExperimentSpec) -> list[str]:
    return [
        f"control__v1__shift_{shift}__{feature}"
        for feature in spec.features
        for shift in SHIFT_SESSIONS
    ]


def _fake_features_for(spec: NatalExperimentSpec) -> list[str]:
    return [
        _fake_feature_name(fake.id, feature)
        for fake in fake_natal_specs()
        for feature in spec.features
    ]


def _evaluate_one_era(
    df: pd.DataFrame,
    *,
    spec: NatalExperimentSpec,
    era_name: str,
    min_n: int,
) -> list[pd.DataFrame]:
    results: list[pd.DataFrame] = []

    jobs = (
        ("registered_real_natal", spec.features, spec.family_name),
        ("shift_null", _shift_features_for(spec), f"{spec.family_name}__shift_null"),
        ("fake_natal", _fake_features_for(spec), f"{spec.family_name}__fake_natal"),
    )
    for test_kind, features, family_name in jobs:
        r = evaluate_categorical_family(
            df,
            features,
            spec.target,
            family_name=family_name,
            min_n=min_n,
        )
        if r.empty:
            continue
        r.insert(0, "hypothesis_id", spec.hypothesis_id)
        r.insert(1, "era", era_name)
        r.insert(2, "test_kind", test_kind)
        results.append(r)
    return results


def _diagnostics(screen: pd.DataFrame) -> pd.DataFrame:
    if screen.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for keys, g in screen.groupby(["hypothesis_id", "era", "test_kind"], dropna=False):
        rows.append(
            {
                "hypothesis_id": keys[0],
                "era": keys[1],
                "test_kind": keys[2],
                "tests": int(len(g)),
                "min_family_fdr": float(g["p_fdr_bh_family"].min()),
                "max_abs_effect_std": float(g["effect_std"].abs().max()),
                "median_abs_effect_std": float(g["effect_std"].abs().median()),
            }
        )
    return pd.DataFrame(rows).sort_values(["hypothesis_id", "era", "test_kind"]).reset_index(drop=True)


def run_historical_exploration(
    raw: pd.DataFrame,
    *,
    out_dir: Path,
    manifest: DataManifest | None = None,
    min_n: int = 100,
) -> dict[str, pd.DataFrame]:
    """Run preregistered historical exploration; there is no holdout path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    base = raw.copy()
    if "symbol" not in base.columns:
        base["symbol"] = "INDEX_000001"

    dataset = add_sse_natal_transit_features(base)
    dataset = add_forward_labels(dataset)
    dataset.to_csv(out_dir / "dataset_natal_transit.csv", index=False)

    registered_features = _all_registered_features()
    analysis_frame = _add_shift_nulls_once(dataset, real_features=registered_features)
    analysis_frame = _add_fake_natal_features_once(analysis_frame, real_features=registered_features)

    parts: list[pd.DataFrame] = []
    for spec in EXPERIMENTS:
        for era_name, start, end in ERAS:
            era = _slice_dates(analysis_frame, start, end)
            parts.extend(_evaluate_one_era(era, spec=spec, era_name=era_name, min_n=min_n))

    screen = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    diag = _diagnostics(screen)
    screen.to_csv(out_dir / "historical_exploratory_screen.csv", index=False)
    diag.to_csv(out_dir / "diagnostic_summary.csv", index=False)

    if manifest is not None:
        (out_dir / "data_manifest.json").write_text(manifest.to_json() + "\n", encoding="utf-8")

    meta = {
        "branch": "SSE_NATAL_V1",
        "historical_status": "EXPLORATORY_ONLY",
        "historical_last_date": "2026-08-14",
        "confirmatory_start": "2026-08-17",
        "real_natal_anchor": SSE_NATAL_V1.anchor.isoformat(),
        "fake_natal_anchors": {x.id: x.anchor.isoformat() for x in fake_natal_specs()},
        "shift_null_sessions": list(SHIFT_SESSIONS),
        "minimum_observations_per_level": min_n,
        "rows": int(len(dataset)),
    }
    (out_dir / "run_metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# SSE_NATAL_V1 × Transit — Historical Exploration",
        "",
        "**Evidence status: exploratory only. No row through 2026-08-14 is a holdout.**",
        "",
        f"Real natal anchor: `{SSE_NATAL_V1.anchor.isoformat()}`",
        "",
        "Controls: shifted-session features at 17/31/47 sessions and fake natal anchors at +17/+31/+47 calendar days.",
        "",
        "## Diagnostic minima",
        "",
    ]
    if diag.empty:
        lines.append("No eligible tests met the sample threshold.")
    else:
        lines.append(diag.to_markdown(index=False))
    lines.extend(
        [
            "",
            "## Gate",
            "Historical anomalies may nominate future hypotheses only. They cannot confirm SSE_NATAL_V1 because the historical outcomes were already exposed before this branch was frozen.",
        ]
    )
    (out_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {"dataset": dataset, "screen": screen, "diagnostics": diag}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SSE_NATAL_V1 historical exploratory research")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--fetch-akshare", action="store_true")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--start", default="19901219")
    parser.add_argument("--end", default="20260814")
    parser.add_argument("--out", type=Path, default=Path("reports/sse_natal_exploratory"))
    parser.add_argument("--min-n", type=int, default=100)
    args = parser.parse_args()

    manifest: DataManifest | None = None
    if args.fetch_akshare:
        raw, manifest = fetch_akshare_index(symbol=args.symbol, start_date=args.start, end_date=args.end)
    else:
        raw = pd.read_csv(args.input)

    result = run_historical_exploration(raw, out_dir=args.out, manifest=manifest, min_n=args.min_n)
    print(f"rows={len(result['dataset'])}")
    print(f"screen_tests={len(result['screen'])}")
    print(f"report={args.out / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
