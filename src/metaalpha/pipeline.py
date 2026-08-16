from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

from .bazi_ziping import add_ziping_features
from .calendar_features import add_gregorian_features
from .controls import add_deterministic_null_controls
from .ganzhi import add_ganzhi_features
from .labels import add_forward_labels
from .natal_transit import add_sse_natal_transit_features
from .validation import evaluate_categorical_feature
from .zpzt_state import add_ziping_state_features
from .zpzt_strength import add_ziping_strength_primitives
from .zpzt_use_v2 import add_ziping_use_v2_features


def build_dataset(
    df: pd.DataFrame,
    include_ziping: bool = False,
    include_natal_transit: bool = False,
) -> pd.DataFrame:
    required = {"date", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    out = df.copy()
    if "symbol" not in out.columns:
        out["symbol"] = "MARKET"
    out = add_gregorian_features(out)
    if include_ziping:
        out = add_ganzhi_features(out)
        out = add_ziping_features(out)
        # v2 is additive and versioned. It does not rewrite the historical v1
        # month-primary features; it records source-constrained 用神变化 primitives.
        out = add_ziping_use_v2_features(out)
        out = add_ziping_strength_primitives(out)
        out = add_ziping_state_features(out)
    if include_natal_transit:
        out = add_sse_natal_transit_features(out)
    out = add_deterministic_null_controls(out)
    out = add_forward_labels(out)
    return out


def run_screen(df: pd.DataFrame, target: str = "ret_fwd_1") -> pd.DataFrame:
    prefixes = (
        "calendar__v1__",
        "control__v1__random_",
        "ganzhi__v2__",
        "zpzt__v1__",
        "zpzt_use__v2__",
        "zpzt_strength__v1__",
        "zpzt_state__v1__",
        "natal__v1__",
        "natal_transit__v1__",
    )
    feature_cols = [c for c in df.columns if c.startswith(prefixes)]
    reports = []
    for feature in feature_cols:
        if df[feature].dtype == object or df[feature].nunique(dropna=True) <= 64:
            r = evaluate_categorical_feature(df, feature, target)
            if not r.empty:
                reports.append(r)
    if not reports:
        return pd.DataFrame()
    return pd.concat(reports, ignore_index=True).sort_values(["p_fdr_bh", "p_value"])


def main() -> None:
    parser = argparse.ArgumentParser(description="MetaAlpha research pipeline")
    parser.add_argument("input", type=Path, help="CSV with date, close and optional symbol/OHLCV")
    parser.add_argument("--out", type=Path, default=Path("reports/latest"))
    parser.add_argument("--target", default="ret_fwd_1")
    parser.add_argument(
        "--ziping",
        action="store_true",
        help="enable Ganzhi + standalone Ziping v1 plus source-constrained 用神变化 v2 features",
    )
    parser.add_argument(
        "--natal-transit",
        action="store_true",
        help="enable frozen SSE_NATAL_V1 natal-chart versus transit relation features",
    )
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(args.input)
    dataset = build_dataset(
        raw,
        include_ziping=args.ziping,
        include_natal_transit=args.natal_transit,
    )
    dataset.to_csv(args.out / "dataset.csv", index=False)

    screen = run_screen(dataset, args.target)
    screen.to_csv(args.out / "univariate_screen.csv", index=False)
    print(f"wrote {len(dataset)} rows to {args.out / 'dataset.csv'}")
    print(f"wrote {len(screen)} screening rows to {args.out / 'univariate_screen.csv'}")


if __name__ == "__main__":
    main()
