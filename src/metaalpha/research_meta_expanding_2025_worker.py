from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .data_sources import fetch_akshare_index
from .hybrid_model import fit_predict_probability, make_ridge_logistic_pipeline
from .market_baseline import BASE_CATEGORICAL, BASE_CONTINUOUS, TARGET_DIRECTION, TARGET_RETURN
from .meta_branch import META_CANDIDATE_FEATURES, META_NEGATIVE_CONTROL_FEATURES, build_meta_historical_dataset


HYPOTHESIS_ID = "META_HIST_EXPANDING_2025_001"
DEFAULT_RAW_START = "19901219"
DEFAULT_TEST_START = "20250101"
DEFAULT_END = "20260817"
MODELS = ("baseline", *META_CANDIDATE_FEATURES.keys(), *META_NEGATIVE_CONTROL_FEATURES.keys())


def _categorical_cols(model_id: str) -> list[str]:
    cols = list(BASE_CATEGORICAL)
    if model_id == "baseline":
        return cols
    if model_id in META_CANDIDATE_FEATURES:
        return cols + list(META_CANDIDATE_FEATURES[model_id])
    if model_id in META_NEGATIVE_CONTROL_FEATURES:
        return cols + list(META_NEGATIVE_CONTROL_FEATURES[model_id])
    raise ValueError(f"unknown model_id: {model_id}")


def run_worker(
    raw: pd.DataFrame,
    *,
    model_id: str,
    test_start: str,
    test_end: str,
    fixed_c: float | None = None,
    chunk_index: int = 0,
    chunk_count: int = 1,
) -> pd.DataFrame:
    if model_id not in MODELS:
        raise ValueError(f"model_id must be one of {MODELS}")
    if chunk_count < 1 or chunk_index < 0 or chunk_index >= chunk_count:
        raise ValueError("invalid chunk_index/chunk_count")

    dataset = build_meta_historical_dataset(raw)
    start_ts = pd.Timestamp(test_start)
    end_ts = pd.Timestamp(test_end)
    all_test_dates = dataset.loc[(dataset["date"] >= start_ts) & (dataset["date"] <= end_ts), "date"].tolist()
    if not all_test_dates:
        raise ValueError("no eligible test dates")

    chunks = np.array_split(np.arange(len(all_test_dates)), chunk_count)
    selected_idx = chunks[chunk_index]
    test_dates = [all_test_dates[int(i)] for i in selected_idx]
    if not test_dates:
        raise ValueError(f"empty chunk {chunk_index}/{chunk_count}")

    categorical = _categorical_cols(model_id)
    rows: list[dict[str, object]] = []

    for i, date in enumerate(test_dates, start=1):
        train = dataset.loc[dataset["date"] < date].copy().reset_index(drop=True)
        test = dataset.loc[dataset["date"] == date].copy().reset_index(drop=True)
        if len(test) != 1:
            raise ValueError(f"expected one test row for {date}, got {len(test)}")
        if len(train) < 1000:
            raise ValueError(f"insufficient expanding training rows before {date}")

        if fixed_c is None:
            p, best_c, _ = fit_predict_probability(
                train,
                test,
                numeric_cols=list(BASE_CONTINUOUS),
                categorical_cols=categorical,
                target_col=TARGET_DIRECTION,
            )
        else:
            best_c = float(fixed_c)
            pipe = make_ridge_logistic_pipeline(list(BASE_CONTINUOUS), categorical, C=best_c)
            y_train = train[TARGET_DIRECTION].astype(int).to_numpy()
            pipe.fit(train[list(BASE_CONTINUOUS) + categorical], y_train)
            p = pipe.predict_proba(test[list(BASE_CONTINUOUS) + categorical])[:, 1]

        rows.append(
            {
                "date": pd.Timestamp(date).strftime("%Y-%m-%d"),
                "model_id": model_id,
                "prob_up": float(p[0]),
                "best_C": float(best_c),
                "training_rows": int(len(train)),
                "training_last_date": train["date"].iloc[-1].strftime("%Y-%m-%d"),
                "target": int(test[TARGET_DIRECTION].iloc[0]),
                "same_session_return": float(test[TARGET_RETURN].iloc[0]),
            }
        )
        if i == 1 or i % 20 == 0 or i == len(test_dates):
            mode = "fixed" if fixed_c is not None else "tuned"
            print(
                f"[{model_id}/{mode}/chunk={chunk_index+1}/{chunk_count}] "
                f"{i}/{len(test_dates)} date={date.date()} C={best_c} p={float(p[0]):.6f}",
                flush=True,
            )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily expanding worker for META_HIST_EXPANDING_2025_001")
    parser.add_argument("--model-id", required=True, choices=MODELS)
    parser.add_argument("--provider", default="sina")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--raw-start", default=DEFAULT_RAW_START)
    parser.add_argument("--test-start", default=DEFAULT_TEST_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path)
    parser.add_argument("--fixed-c", type=float)
    parser.add_argument("--chunk-index", type=int, default=0)
    parser.add_argument("--chunk-count", type=int, default=1)
    args = parser.parse_args()

    raw, manifest = fetch_akshare_index(
        symbol=args.symbol,
        start_date=args.raw_start,
        end_date=args.end,
        provider=args.provider,
    )
    result = run_worker(
        raw,
        model_id=args.model_id,
        test_start=args.test_start,
        test_end=args.end,
        fixed_c=args.fixed_c,
        chunk_index=args.chunk_index,
        chunk_count=args.chunk_count,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.out, index=False)
    if args.manifest_out is not None:
        args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_out.write_text(manifest.to_json() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
