# MetaAlpha v1 Historical Closeout — 2026-08-19

**Status: HISTORICAL V1 CLOSED / NO FURTHER RESCUE TUNING.**

This closeout combines the completed fixed-C=0.01 daily-expanding reconstruction from 2025-01-01 through 2026-08-17 with the already completed calendar, matched-null, hash-ensemble, temporal-stability and regime diagnostics. It is retrospective and cannot alter META_FWD_001.

## Daily-expanding fixed-C results

Common baseline: LogLoss **0.691576**, Brier **0.249208**, n=393.

| branch | LogLoss | ΔLL vs baseline | Brier | ΔBrier vs baseline | frozen interpretation |
|---|---:|---:|---:|---:|---|
| ziping | 0.690857 | +0.000719 | 0.248843 | +0.000365 | weak regime-dependent residual; below frozen effect-size gates |
| qimen | 0.691272 | +0.000304 | 0.249035 | +0.000173 | below frozen effect-size gates |
| cycle | 0.691287 | +0.000289 | 0.249046 | +0.000162 | below frozen effect-size gates; consistent with generic time encoding |
| meihua | 0.696081 | -0.004505 | 0.251443 | -0.002235 | historical failure |
| liuyao_hash negative control | 0.688998 | +0.002578 | 0.247936 | +0.001272 | negative control only; not a traditional claim |

Frozen effect-size references from META_FWD_001 are ΔLogLoss >= 0.001 and ΔBrier >= 0.0005. **No traditional v1 branch clears both thresholds in this 393-session daily-expanding reconstruction.**

## Specificity evidence already completed

- 248 dense shifts: real Cycle ~88.7th percentile, Ziping ~87.1st, Qimen ~65.7th, Meihua 0th. Real traditional alignment is not extreme enough to establish mapping specificity.
- 100-seed hash ensemble: about 26% of generic deterministic hash encodings beat baseline LogLoss in the 393-session retrospective sample; the frozen LIUYAO_HASH_V1 is around the 95th percentile and is consistent with a lucky frozen random encoding.
- Rich Gregorian calendar controls absorb part of the apparent symbolic increment; Ziping's absolute residual versus the original market baseline is small.
- Temporal slices show sign/regime instability: Ziping is negative in 2025 and positive in 2026; Cycle/Qimen also reverse or weaken across periods.

## Closeout decision

1. MetaAlpha v1 historical school-ranking research is closed.
2. MEIHUA_TIME_V1 is historical FAIL and must not be rescued under the same ID.
3. QIMEN_V1 and CYCLE_V1 are not promoted as traditional-specific factors.
4. Ziping remains only a weak residual candidate; it has no demonstrated traditional-time specificity.
5. No new 神煞 / 纳音 / 旺衰 / 卦辞评分 / school variants may be added to v1 based on observed historical outcomes.
6. New formulations require a new hypothesis/family ID and preregistration before outcomes are inspected.
7. Scientific v2 is specificity-first: utility versus baseline is necessary but insufficient; traditional mapping must also beat a matched-null family, remain temporally stable, replicate cross-market, and survive future-only evidence.
8. META_FWD_001 continues unchanged as the primary frozen prospective experiment.

The exact daily inner-CV Baseline-vs-Ziping reconstruction is retained as a final robustness check, not as permission to reopen v1 if results are favorable.
