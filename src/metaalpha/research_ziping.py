from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

import pandas as pd

from .controls import add_shifted_feature
from .data_sources import DataManifest, fetch_akshare_index
from .pipeline import build_dataset
from .validation import evaluate_categorical_family, walk_forward_categorical_stability


@dataclass(frozen=True)
class ExperimentSpec:
    hypothesis_id: str
    target: str
    features: tuple[str, ...]
    family_name: str


EXPERIMENTS: tuple[ExperimentSpec, ...] = (
    ExperimentSpec(
        hypothesis_id="ZIPING_001",
        target="ret_fwd_1",
        family_name="ziping_pattern_v1",
        features=(
            "zpzt__v1__month_primary_ten_god",
            "zpzt__v1__pattern_candidate",
            "zpzt__v1__use_mode",
            "zpzt__v1__month_hidden_transmitted_count",
            "zpzt__v1__month_disruption_count",
        ),
    ),
    ExperimentSpec(
        hypothesis_id="ZIPING_002",
        target="vol_fwd_5",
        family_name="ziping_structure_v1",
        features=(
            "zpzt__v1__route_hit_count",
            "zpzt__v1__month_clash",
            "zpzt__v1__month_harm",
            "zpzt__v1__month_break",
            "zpzt__v1__month_punishment",
        ),
    ),
    ExperimentSpec(
        hypothesis_id="ZIPING_003",
        target="ret_fwd_1",
        family_name="ziping_state_return_v1",
        features=(
            "zpzt_state__v1__state",
            "zpzt_state__v1__formation_hit",
            "zpzt_state__v1__failure_hit",
            "zpzt_state__v1__rescue_hit",
            "zpzt_state__v1__requires_strength",
        ),
    ),
    ExperimentSpec(
        hypothesis_id="ZIPING_004",
        target="vol_fwd_5",
        family_name="ziping_state_risk_v1",
        features=(
            "zpzt_state__v1__state",
            "zpzt_state__v1__formation_hit",
            "zpzt_state__v1__failure_hit",
            "zpzt_state__v1__rescue_hit",
            "zpzt_state__v1__requires_strength",
        ),
    ),
)


PARTITIONS = (
    ("development", None, "2014-12-31"),
    ("validation", "2015-01-01", "2020-12-31"),
    ("sealed_holdout_v1", "2021-01-01", None),
)

SHIFT_SESSIONS = (17, 31, 47)


def _slice_dates(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    dates = pd.to_datetime(df["date"], errors="raise")
    mask = pd.Series(True, index=df.index)
    if start is not None:
        mask &= dates >= pd.Timestamp(start)
    if end is not None:
        mask &= dates <= pd.Timestamp(end)
    return df.loc[mask].copy()


def _add_shift_nulls(df: pd.DataFrame, features: Iterable[str]) -> tuple[pd.DataFrame, list[str]]:
    out = df.copy()
    null_features: list[str] = []
    for feature in features:
        for shift in SHIFT_SESSIONS:
            out = add_shifted_feature(out, feature, shift_rows=shift)
            null_features.append(f"control__v1__shift_{shift}__{feature}")
    return out, null_features


def _screen_partition(
    df: pd.DataFrame,
    *,
    spec: ExperimentSpec,
    partition_name: str,
    min_n: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    real = evaluate_categorical_family(
        df,
        spec.features,
        spec.target,
        family_name=spec.family_name,
        min_n=min_n,
    )
    if not real.empty:
        real.insert(0, "hypothesis_id", spec.hypothesis_id)
        real.insert(1, "partition", partition_name)
        real.insert(2, "test_kind", "registered")

    with_nulls, null_features = _add_shift_nulls(df, spec.features)
    null = evaluate_categorical_family(
        with_nulls,
        null_features,
        spec.target,
        family_name=f"{spec.family_name}__shift_null",
        min_n=min_n,
    )
    if not null.empty:
        null.insert(0, "hypothesis_id", spec.hypothesis_id)
        null.insert(1, "partition", partition_name)
        null.insert(2, "test_kind", "shift_null")
    return real, null


def _walk_forward_for_spec(df: pd.DataFrame, spec: ExperimentSpec) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for feature in spec.features:
        r = walk_forward_categorical_stability(
            df,
            feature=feature,
            target=spec.target,
            min_train=1500,
            test_size=500,
            min_n=20,
        )
        if r.empty:
            continue
        r.insert(0, "hypothesis_id", spec.hypothesis_id)
        parts.append(r)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _diagnostic_summary(screen: pd.DataFrame) -> pd.DataFrame:
    if screen.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    group_cols = ["hypothesis_id", "partition", "test_kind"]
    for keys, g in screen.groupby(group_cols, dropna=False):
        p_col = "p_fdr_bh_family"
        rows.append(
            {
                "hypothesis_id": keys[0],
                "partition": keys[1],
                "test_kind": keys[2],
                "tests": int(len(g)),
                "min_family_fdr": float(g[p_col].min()),
                "max_abs_effect_std": float(g["effect_std"].abs().max()),
                "median_abs_effect_std": float(g["effect_std"].abs().median()),
            }
        )
    return pd.DataFrame(rows).sort_values(group_cols).reset_index(drop=True)


def run_first_sse_experiment(
    raw: pd.DataFrame,
    *,
    out_dir: Path,
    manifest: DataManifest | None = None,
    min_n: int = 100,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    dataset = build_dataset(raw, include_ziping=True)
    dataset.to_csv(out_dir / "dataset.csv", index=False)

    all_screens: list[pd.DataFrame] = []
    all_walk: list[pd.DataFrame] = []

    for spec in EXPERIMENTS:
        for partition_name, start, end in PARTITIONS:
            part = _slice_dates(dataset, start, end)
            real, null = _screen_partition(
                part,
                spec=spec,
                partition_name=partition_name,
                min_n=min_n,
            )
            if not real.empty:
                all_screens.append(real)
            if not null.empty:
                all_screens.append(null)

        walk = _walk_forward_for_spec(dataset, spec)
        if not walk.empty:
            all_walk.append(walk)

    screen = pd.concat(all_screens, ignore_index=True) if all_screens else pd.DataFrame()
    walk_forward = pd.concat(all_walk, ignore_index=True) if all_walk else pd.DataFrame()
    diagnostics = _diagnostic_summary(screen)

    screen.to_csv(out_dir / "registered_and_null_screens.csv", index=False)
    walk_forward.to_csv(out_dir / "walk_forward_stability.csv", index=False)
    diagnostics.to_csv(out_dir / "diagnostic_summary.csv", index=False)

    if manifest is not None:
        (out_dir / "data_manifest.json").write_text(manifest.to_json() + "\n", encoding="utf-8")

    run_meta = {
        "experiment_ids": [x.hypothesis_id for x in EXPERIMENTS],
        "partitions": [x[0] for x in PARTITIONS],
        "sealed_holdout_v1": {
            "start": "2021-01-01",
            "status_after_this_run": "BURNED_FOR_V1_AFTER_FIRST_EVALUATION",
            "rule": "No v1 rule/weight tuning may claim this interval as unseen after this run.",
        },
        "shift_null_sessions": list(SHIFT_SESSIONS),
        "minimum_observations_per_level": min_n,
        "rows": int(len(dataset)),
        "first_date": pd.to_datetime(dataset["date"]).min().strftime("%Y-%m-%d"),
        "last_date": pd.to_datetime(dataset["date"]).max().strftime("%Y-%m-%d"),
    }
    (out_dir / "run_metadata.json").write_text(
        json.dumps(run_meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary_lines = [
        "# MetaAlpha — SSE Ziping First Experiment",
        "",
        "This report is a preregistered statistical experiment, not an investment recommendation.",
        "",
        "## Data",
        f"- rows: {len(dataset)}",
        f"- first session: {run_meta['first_date']}",
        f"- last session: {run_meta['last_date']}",
        "",
        "## Partitions",
        "- development: through 2014-12-31",
        "- validation: 2015-01-01 through 2020-12-31",
        "- sealed_holdout_v1: 2021-01-01 onward",
        "",
        "The v1 holdout is considered burned after this first evaluation. Any subsequent rule change must be versioned and cannot reuse it as unseen evidence.",
        "",
        "## Diagnostics",
    ]
    if diagnostics.empty:
        summary_lines.append("No eligible tests met the minimum sample requirement.")
    else:
        summary_lines.append("")
        summary_lines.append(diagnostics.to_markdown(index=False))
    summary_lines.extend(
        [
            "",
            "## Interpretation gate",
            "A low historical p-value alone is not acceptance. The registered family must beat null controls, retain direction/effect through later partitions, and survive future forward testing.",
        ]
    )
    (out_dir / "SUMMARY.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return {
        "dataset": dataset,
        "screen": screen,
        "walk_forward": walk_forward,
        "diagnostics": diagnostics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MetaAlpha first SSE Ziping Zhenquan experiment")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="normalized/raw-compatible CSV with date/close")
    source.add_argument("--fetch-akshare", action="store_true", help="fetch SSE index history via AKShare index_zh_a_hist")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--start", default="19901219")
    parser.add_argument("--end", default="22220101")
    parser.add_argument("--out", type=Path, default=Path("reports/sse_ziping_first"))
    parser.add_argument("--min-n", type=int, default=100)
    args = parser.parse_args()

    manifest: DataManifest | None = None
    if args.fetch_akshare:
        raw, manifest = fetch_akshare_index(symbol=args.symbol, start_date=args.start, end_date=args.end)
    else:
        raw = pd.read_csv(args.input)

    results = run_first_sse_experiment(raw, out_dir=args.out, manifest=manifest, min_n=args.min_n)
    print(f"rows={len(results['dataset'])}")
    print(f"screen_tests={len(results['screen'])}")
    print(f"report={args.out / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
