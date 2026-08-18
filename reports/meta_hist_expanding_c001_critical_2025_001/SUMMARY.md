# META_HIST_EXPANDING_C001_CRITICAL_2025_001

**RETROSPECTIVE / DESCRIPTIVE / same fixed-C daily-expanding definition as META_HIST_EXPANDING_C001_2025_001.**

| model | n | LogLoss | Brier | Accuracy | ΔLL vs baseline | ΔBrier vs baseline |
|---|---:|---:|---:|---:|---:|---:|
| liuyao_hash | 393 | 0.688998 | 0.247936 | 0.5242 | +0.002578 | +0.001272 |
| ziping | 393 | 0.690857 | 0.248843 | 0.5318 | +0.000719 | +0.000365 |
| baseline | 393 | 0.691576 | 0.249208 | 0.5420 | +0.000000 | +0.000000 |

## Calendar-year slices

| year | model | n | LogLoss | ΔLL vs same-year baseline |
|---:|---|---:|---:|---:|
| 2025 | baseline | 243 | 0.694504 | +0.000000 |
| 2025 | ziping | 243 | 0.695079 | -0.000575 |
| 2025 | liuyao_hash | 243 | 0.692341 | +0.002164 |
| 2026 | baseline | 150 | 0.686831 | +0.000000 |
| 2026 | ziping | 150 | 0.684017 | +0.002815 |
| 2026 | liuyao_hash | 150 | 0.683582 | +0.003249 |

This fast lane exists only to obtain the three most decision-relevant daily-expanding reconstructions sooner. It does not alter META_FWD_001 and does not replace the six-model aggregate.
