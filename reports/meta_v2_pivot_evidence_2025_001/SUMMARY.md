# META_V2_PIVOT_EVIDENCE_2025_001 — Evidence synthesis for the specificity-first pivot

**RETROSPECTIVE / DECISION MEMO / DOES NOT MODIFY META_FWD_001**

## Executive decision

The current historical evidence does not support treating Cycle, Ziping, Qimen or Meihua V1 as uniquely aligned traditional market factors. MetaAlpha v2 should treat traditional mappings as members of a broader deterministic time-encoding hypothesis class and require specificity versus matched nulls before any traditional interpretation.

Ziping remains the strongest traditional residual candidate, but its remaining evidence is weak, regime-dependent and non-specific.

## Evidence 1 — Rich Gregorian calendar stress

On 393 sessions from 2025-01-02 through 2026-08-17, adding richer ordinary Gregorian calendar controls absorbed part of the earlier apparent symbolic gain.

Against the original market baseline LogLoss 0.692936:

- rich-calendar + Ziping: 0.692419, only +0.000517 absolute improvement versus the original market baseline;
- rich-calendar + Hash: 0.691294, +0.001642;
- rich-calendar + Cycle: 0.693971, worse than the original market baseline;
- rich-calendar + Qimen: 0.693284, worse than the original market baseline;
- rich-calendar + Meihua: 0.698187, materially worse.

Conclusion: simple Gregorian seasonality explains a meaningful part, but not all, of the Ziping/Hash residual.

## Evidence 2 — Dense shifted-state specificity

Each traditional state path was compared with every integer trading-session shift from 5 through 252, 248 shifted copies per branch, with identical model capacity and C=0.01.

- Cycle exact alignment percentile: 88.7%; 28 shifted copies were better.
- Ziping: 87.1%; 32 shifted copies were better.
- Qimen: 65.7%; 85 shifted copies were better.
- Meihua: 0%; all 248 shifted copies were better.

Conclusion: none of the current traditional mappings shows strong exact-date alignment specificity. Ziping's exact mapping is not rare enough within displaced copies to support a traditional-phase claim.

## Evidence 3 — 100-seed hash negative-control ensemble

One hundred deterministic SHA256 date encodings with the same representation capacity as the frozen hash control were evaluated.

- 26% beat the market baseline in LogLoss by chance within this historical sample;
- mean random-seed improvement was negative;
- frozen LIUYAO_HASH_V1 sat around the 95th percentile of the 100-seed null distribution;
- seed 4 achieved ΔLogLoss about +0.004981, substantially stronger than current traditional candidates;
- roughly 15/100 random hashes exceeded the earlier fixed-fit Ziping LogLoss improvement.

Conclusion: a historically impressive date encoding can arise from a lucky deterministic partition. A single negative control is insufficient; the null distribution itself must be part of the scientific test.

## Evidence 4 — Fixed-C daily expanding reconstruction from 2025-01-01

Critical-trio fast reconstruction refits on every trading day using only prior eligible rows, with frozen C=0.01.

| model | LogLoss | Brier | ΔLL vs expanding baseline | ΔBrier vs expanding baseline |
|---|---:|---:|---:|---:|
| baseline | 0.691576 | 0.249208 | 0 | 0 |
| ziping | 0.690857 | 0.248843 | +0.000719 | +0.000365 |
| liuyao_hash | 0.688998 | 0.247936 | +0.002578 | +0.001272 |

The frozen META_FWD_001 full-sample effect-size thresholds are ΔLogLoss >= 0.001 and ΔBrier >= 0.0005. The daily-expanding Ziping approximation fails both thresholds before bootstrap or multiplicity correction.

Year slices reinforce instability:

- 2025 Ziping ΔLL versus same-year expanding baseline: -0.000575;
- 2026 Ziping: +0.002815;
- 2025 Hash: +0.002164;
- 2026 Hash: +0.003249.

Conclusion: daily updating does not reveal a stable Ziping edge. The full-period residual is dominated by 2026 behavior.

## Combined interpretation

The evidence is more consistent with temporary synchronization between market regimes and deterministic time partitions than with a stable, uniquely aligned traditional factor.

A traditional branch should therefore pass two conceptually separate gates:

1. **Utility gate:** improve a strong ordinary-market baseline under past-only validation.
2. **Specificity gate:** outperform a preregistered matched-null distribution of equally complex arbitrary/displaced time encodings.

Only after both gates, temporal stability, cross-market replication and future-only evidence may the traditional mapping itself receive interpretive credit.

## Current branch disposition

- Meihua TIME_V1: historical failure; freeze and do not rescue.
- Qimen V1: historical weak/unstable; deprioritize.
- Cycle V1: generic temporal-encoding candidate, not traditional-specific evidence.
- Ziping: retain only as a weak residual candidate; exact alignment specificity failed and daily-expanding effect size is below the frozen META gate in the current quick reconstruction.
- LIUYAO_HASH_V1: negative control only; its strong historical result is consistent with a lucky frozen random encoding.

## Next admissible evidence

- complete six-model fixed-C daily-expanding reconstruction;
- complete exact daily-expanding reconstruction with daily frozen inner-CV C selection;
- continue META_FWD_001 unchanged, counting only records that satisfy its immutable pre-anchor eligibility rules.

No new symbolic feature mining is justified by the current evidence.
