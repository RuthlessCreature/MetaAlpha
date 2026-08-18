# META_TEMPORAL_STABILITY_2025_001 — Temporal stability diagnostic

**RETROSPECTIVE / DESCRIPTIVE ONLY. Does not modify META_FWD_001.**

Source: `reports/meta_hist_2025_001/metrics_by_slice.csv`, fixed-fit 2025-01-02 through 2026-08-17 retrospective predictions.

## Year-level LogLoss

| model | 2025 | 2026 | year-to-year interpretation |
|---|---:|---:|---|
| baseline | 0.695253 | 0.689183 | reference |
| cycle | 0.691630 | 0.693473 | wins 2025, loses 2026 |
| ziping | 0.695650 | 0.685479 | roughly flat/slightly worse in 2025, strongly better in 2026 |
| qimen | 0.691239 | 0.694085 | wins 2025, loses 2026 |
| meihua | 0.700193 | 0.693351 | loses both years |
| liuyao_hash | 0.693263 | 0.686428 | beats baseline in both years, but is a negative control and later shown to be a lucky ~95th-percentile hash seed |

## Quarter win counts versus baseline

A quarter counts as a win only when its LogLoss is lower than the baseline in the same quarter.

| model | quarters beating baseline | total quarters | pattern |
|---|---:|---:|---|
| cycle | 4 | 7 | 2025Q2/Q3/Q4 and 2026Q3; strong sign reversals |
| ziping | 4 | 7 | 2025Q2/Q3 and 2026Q1/Q2; loses 2025Q1/Q4 and 2026Q3 |
| qimen | 3 | 7 | only 2025Q1/Q2/Q4; loses every observed 2026 quarter |
| meihua | 2 | 7 | isolated 2025Q2 and 2026Q1 only |
| liuyao_hash | 5 | 7 | strongest apparent stability among tested encodings, but remains a negative control |

## Key conclusion

The fixed-fit historical gains are strongly time-dependent. In particular, Ziping's full-period advantage is not a uniform effect: it is essentially absent in 2025 and becomes large in 2026. Cycle and Qimen show the opposite pattern, winning in 2025 and reversing in 2026.

This behavior is inconsistent with treating any current symbolic branch as a stable universal directional factor. It is compatible with temporary synchronization between deterministic time partitions and changing market regimes.

This diagnostic is not a new hypothesis and must not be used to tune symbolic rules. The exact daily-expanding reconstructions remain the next robustness check.
