from __future__ import annotations

import argparse
import json
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd

from .data_sources import DataManifest, fetch_akshare_index


DEFAULT_PROVIDERS = ("eastmoney_direct", "sina", "tencent")


def compare_provider_frames(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    left_name: str,
    right_name: str,
) -> tuple[dict[str, object], pd.DataFrame]:
    cols = ["date", "open", "high", "low", "close"]
    a = left[cols].copy().sort_values("date")
    b = right[cols].copy().sort_values("date")
    a["ret1"] = a["close"].pct_change()
    b["ret1"] = b["close"].pct_change()
    m = a.merge(b, on="date", how="inner", suffixes=("_left", "_right"))
    if m.empty:
        raise ValueError(f"no overlapping dates between {left_name} and {right_name}")

    m["close_abs_diff"] = (m["close_left"] - m["close_right"]).abs()
    m["ret1_abs_diff"] = (m["ret1_left"] - m["ret1_right"]).abs()
    metrics = {
        "left_provider": left_name,
        "right_provider": right_name,
        "left_rows": int(len(left)),
        "right_rows": int(len(right)),
        "common_dates": int(len(m)),
        "first_common_date": pd.to_datetime(m["date"]).min().strftime("%Y-%m-%d"),
        "last_common_date": pd.to_datetime(m["date"]).max().strftime("%Y-%m-%d"),
        "mean_close_abs_diff": float(m["close_abs_diff"].mean()),
        "max_close_abs_diff": float(m["close_abs_diff"].max()),
        "close_diff_gt_0_1": int((m["close_abs_diff"] > 0.1).sum()),
        "close_diff_gt_1": int((m["close_abs_diff"] > 1.0).sum()),
        "ret_diff_gt_1bp": int((m["ret1_abs_diff"] > 0.0001).sum()),
        "ret_diff_gt_10bp": int((m["ret1_abs_diff"] > 0.001).sum()),
        "ret_diff_gt_100bp": int((m["ret1_abs_diff"] > 0.01).sum()),
        "max_ret1_abs_diff": float(m["ret1_abs_diff"].max(skipna=True)),
    }
    top = m.nlargest(50, "ret1_abs_diff").copy()
    top.insert(0, "left_provider", left_name)
    top.insert(1, "right_provider", right_name)
    return metrics, top


def run_reconciliation(
    *,
    out_dir: Path,
    symbol: str = "000001",
    start_date: str = "19901219",
    end_date: str = "20260814",
    providers: tuple[str, ...] = DEFAULT_PROVIDERS,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    frames: dict[str, pd.DataFrame] = {}
    manifests: dict[str, DataManifest] = {}
    errors: dict[str, str] = {}

    for provider in providers:
        try:
            frame, manifest = fetch_akshare_index(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                provider=provider,
            )
            frames[provider] = frame
            manifests[provider] = manifest
        except Exception as exc:  # pragma: no cover - network dependent
            errors[provider] = f"{type(exc).__name__}: {exc}"

    if len(frames) < 2:
        raise RuntimeError(f"reconciliation requires at least two providers; successes={list(frames)}, errors={errors}")

    metric_rows: list[dict[str, object]] = []
    disagreements: list[pd.DataFrame] = []
    for left_name, right_name in combinations(frames, 2):
        metrics, top = compare_provider_frames(
            frames[left_name],
            frames[right_name],
            left_name=left_name,
            right_name=right_name,
        )
        metric_rows.append(metrics)
        disagreements.append(top)

    metrics_df = pd.DataFrame(metric_rows)
    top_df = pd.concat(disagreements, ignore_index=True) if disagreements else pd.DataFrame()
    metrics_df.to_csv(out_dir / "pairwise_metrics.csv", index=False)
    top_df.to_csv(out_dir / "top_return_disagreements.csv", index=False)

    manifest_payload = {
        name: manifest.to_dict() for name, manifest in manifests.items()
    }
    (out_dir / "provider_manifests.json").write_text(
        json.dumps(manifest_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "provider_errors.json").write_text(
        json.dumps(errors, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# A-share Index Cross-Provider Reconciliation",
        "",
        "This is a data-quality report. It does not choose a provider based on which one improves a research result.",
        "",
        "## Successful providers",
        "",
    ]
    for name, manifest in manifests.items():
        lines.append(f"- `{name}`: {manifest.rows} rows, {manifest.first_date} to {manifest.last_date}, SHA256 `{manifest.canonical_sha256}`")
    if errors:
        lines.extend(["", "## Provider failures", ""])
        for name, err in errors.items():
            lines.append(f"- `{name}`: {err}")
    lines.extend(["", "## Pairwise metrics", "", metrics_df.to_markdown(index=False), ""])
    lines.extend(
        [
            "## Canonicalization rule",
            "",
            "MetaAlpha must not switch providers automatically inside confirmatory comparisons. A provider must be pinned before a confirmatory run. Auto fallback is availability-only and marks the dataset as a different provenance object.",
        ]
    )
    (out_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "frames": frames,
        "manifests": manifests,
        "errors": errors,
        "metrics": metrics_df,
        "top_disagreements": top_df,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile A-share index history across pinned AKShare providers")
    parser.add_argument("--symbol", default="000001")
    parser.add_argument("--start", default="19901219")
    parser.add_argument("--end", default="20260814")
    parser.add_argument("--out", type=Path, default=Path("reports/data_reconciliation"))
    args = parser.parse_args()
    result = run_reconciliation(
        out_dir=args.out,
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end,
    )
    print(f"successful_providers={list(result['frames'])}")
    print(f"pairwise_comparisons={len(result['metrics'])}")
    print(f"report={args.out / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
