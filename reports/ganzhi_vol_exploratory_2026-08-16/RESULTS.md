# GANZHI_VOL_001 — Direct Ganzhi / Solar-Term Volatility Historical Results

Run date: 2026-08-16  
Workflow run: `31946816076`  
Commit evaluated: `0133ac1bfd7d7063555ead40d77945ed9052c0dd`  
Artifact ID: `9263524891`  
Artifact ZIP SHA256: `ca7bf89ede13029cd23ab691cda5961f2e532edea3b3615cb64d05a458b8a761`

## 1. Executive decision

**GANZHI_VOL_001 fails its preregistered exploratory-interest gate.**

No forward-only volatility experiment is opened from this historical run.

Several direct Chinese-calendar blocks become strongly associated with future five-session volatility in 2015-2020 and especially 2021-2026. However, the evidence fails the stronger tests that were frozen before the run:

1. no registered block is significant over the full 1990-2026 history after family correction;
2. the strongest late-era registered blocks are frequently matched or exceeded by their 17/31/47-session shifted controls;
3. the five non-overlapping residue-class checks almost entirely fail;
4. major solar-term coefficients reverse sign across eras rather than retaining one stable volatility relationship.

The defensible conclusion is **regime-specific synchronization, not a stable calendar-cycle volatility factor**.

## 2. Data and frozen target

- market: Shanghai Composite `000001`;
- provider: pinned Sina via `ak.stock_zh_index_daily`;
- AKShare version: `1.18.84`;
- first session: `1990-12-19`;
- last session: `2026-08-14`;
- observations: `8,704`;
- canonical normalized-data SHA256: `697af81a200060d42b04fa7a79b92fb8287e709ae10baf0825ae301fb4af5aa1`;
- calendar engine: `lunar_python==1.4.8`;
- feature anchor: `09:25 Asia/Shanghai`;
- raw target: realized standard deviation of exactly the one-session returns `t+1..t+5`;
- primary target: natural log of that future five-session realized volatility.

All market baseline variables are available no later than `t-1` close. The current session's close and realized return are not used in the 09:25 baseline.

## 3. Frozen baseline and registered blocks

Baseline:

- lagged log realized volatility over the previous 5 sessions;
- lagged log realized volatility over the previous 20 sessions;
- previous session absolute return;
- normalized secular time and squared normalized time;
- Gregorian weekday fixed effects;
- Gregorian month fixed effects.

Registered calendar blocks:

1. 24 previous-solar-term intervals;
2. solar-term phase quartile;
3. smooth solar-term phase sine/cosine block;
4. 60 day pillars;
5. 10 day stems;
6. 12 day branches;
7. 10 month stems;
8. 12 month branches;
9. `jie` versus `qi` half-cycle type.

Inference:

- incremental OLS block tests;
- Newey-West/HAC covariance with `maxlags=20` for full daily samples;
- Benjamini-Hochberg correction across the 9 registered blocks within each era;
- 17/31/47-session shifted versions of every block as deterministic null controls;
- bounded eras purge their final 5 sessions;
- original trading-session index modulo 5 creates five non-overlapping future-window robustness samples;
- identifiability requires a full-rank design and full-rank HAC restriction covariance.

All tests in this run satisfy the identifiability QC. There are **zero invalid inference rows**.

## 4. Preregistered gate result

| Block | Full-history BH-FDR | Later eras with BH-FDR <= 0.10 | Later eras beating all 3 shifted controls | Non-overlap residues with BH-FDR <= 0.10 | Gate |
|---|---:|---:|---:|---:|---:|
| solar_term_24 | 0.966111 | 2 | 0 | 0 | FAIL |
| solar_term_phase_quartile | 0.966111 | 0 | 2 | 0 | FAIL |
| solar_term_smooth | 0.966111 | 1 | 0 | 0 | FAIL |
| day_pillar_60 | 0.966111 | 2 | 1 | 1 | FAIL |
| day_stem_10 | 0.966111 | 0 | 0 | 0 | FAIL |
| day_branch_12 | 0.966111 | 0 | 1 | 0 | FAIL |
| month_stem_10 | 0.966111 | 1 | 1 | 0 | FAIL |
| month_branch_12 | 0.966111 | 1 | 0 | 0 | FAIL |
| jie_or_qi | 0.966111 | 0 | 0 | 0 | FAIL |

No block passes the complete frozen gate.

## 5. Era-level registered evidence

Registered family minimum BH-FDR:

| Era | Minimum registered BH-FDR | Maximum registered incremental R² |
|---|---:|---:|
| 1990-2004 | 0.874890 | 0.014529 |
| 2005-2014 | 0.370031 | 0.019042 |
| 2015-2020 | 0.004388 | 0.029043 |
| 2021-2026 | 4.641607e-8 | 0.058992 |
| Full history | 0.966111 | 0.004049 |

The late-era significance is real as a descriptive historical association, but it is not stable across the full sample.

### 2015-2020

Notable registered blocks:

- `day_pillar_60`: raw p ≈ `0.000488`, family BH-FDR ≈ `0.004388`;
- `solar_term_24`: raw p ≈ `0.02745`, family BH-FDR ≈ `0.09034`;
- `solar_term_smooth`: raw p ≈ `0.03011`, family BH-FDR ≈ `0.09034`.

### 2021-2026

Notable registered blocks:

- `solar_term_24`: raw p ≈ `5.16e-9`, family BH-FDR ≈ `4.64e-8`, incremental R² ≈ `0.05899`;
- `month_branch_12`: raw p ≈ `0.000395`, family BH-FDR ≈ `0.001447`;
- `month_stem_10`: raw p ≈ `0.000482`, family BH-FDR ≈ `0.001447`;
- `day_pillar_60`: raw p ≈ `0.01705`, family BH-FDR ≈ `0.03835`.

These values are not promoted because the controls and stability requirements fail.

## 6. Shifted controls are frequently stronger

The preregistered rule required the registered block's raw p-value to beat all three shifted versions in at least two later eras. No serious late-era candidate satisfies that condition.

### `solar_term_24`

2015-2020:

- registered p ≈ `0.02745`;
- +17-session shifted p ≈ `8.69e-6`;
- +47-session shifted p ≈ `0.001316`.

2021-2026:

- registered p ≈ `5.16e-9`;
- +31-session shifted p ≈ `4.99e-14`.

A displaced solar-term state is therefore stronger than the source-aligned state in both late eras.

### `day_pillar_60`

2015-2020:

- registered p ≈ `0.000488`;
- +17 shift ≈ `0.000812`;
- +31 shift ≈ `1.77e-5`;
- +47 shift ≈ `8.99e-5`.

2021-2026:

- registered p ≈ `0.01705`;
- +17 shift ≈ `0.01985`;
- +31 shift ≈ `0.001412`;
- +47 shift ≈ `1.51e-5`.

The registered 60-day pillar block is not phase-specific enough to survive displaced-cycle competition.

## 7. Non-overlapping future-window robustness fails

The full eligible history was split by original trading-session index modulo 5. Within each residue class, `t+1..t+5` future-volatility windows do not overlap.

Family BH-FDR by residue:

| Block | Residue 0 | Residue 1 | Residue 2 | Residue 3 | Residue 4 |
|---|---:|---:|---:|---:|---:|
| solar_term_24 | 0.9923 | 0.8820 | 0.9891 | 0.8837 | 0.7780 |
| solar_term_phase_quartile | 0.9923 | 0.8820 | 0.9891 | 0.8930 | 0.2329 |
| solar_term_smooth | 0.9923 | 0.8781 | 0.9891 | 0.8930 | 0.5398 |
| day_pillar_60 | **0.01019** | 0.7225 | 0.9891 | 0.8837 | 0.5398 |
| day_stem_10 | 0.5046 | 0.8391 | 0.9891 | 0.8930 | 0.7780 |
| day_branch_12 | 0.9923 | 0.8820 | 0.9891 | 0.8930 | 0.9442 |
| month_stem_10 | 0.9923 | 0.8820 | 0.9891 | 0.8930 | 0.9608 |
| month_branch_12 | 0.9923 | 0.8820 | 0.9891 | 0.8930 | 0.9442 |
| jie_or_qi | 0.9923 | 0.8820 | 0.7599 | 0.3341 | 0.3967 |

Only one block in one residue class passes 0.10. The preregistered requirement was at least three of five residues for the same block.

## 8. Solar-term direction reverses across regimes

The 24-term block is particularly useful for diagnosis because its strongest late-era association changes direction rather than preserving one stable effect.

Using `冬至` as the categorical reference level, selected conditional log-volatility coefficients are:

| Solar-term interval | 1990-2004 | 2005-2014 | 2015-2020 | 2021-2026 |
|---|---:|---:|---:|---:|
| 夏至 | +0.042 | +0.097 | **+0.893** | **-0.880** |
| 小满 | -0.082 | +0.346 | +0.387 | **-1.128** |
| 芒种 | -0.348 | +0.249 | **+0.742** | **-1.058** |
| 大寒 | -0.213 | +0.351 | +0.291 | +0.309 |
| 立夏 | +0.387 | +0.347 | +0.269 | **-0.782** |
| 小暑 | +0.230 | +0.057 | +0.519 | **-0.795** |
| 惊蛰 | -0.382 | +0.010 | +0.391 | +0.374 |

The dramatic 2015-2020 positive coefficients for several summer solar-term intervals reverse sharply negative in 2021-2026.

This is not the behavior expected from a stable phase-specific volatility factor. It is consistent with calendar phase becoming temporarily synchronized with a changing market-volatility regime and then losing or reversing that synchronization.

Individual category coefficients are diagnostic, not separately multiplicity-adjusted claims; the registered inference unit is the complete block.

## 9. Interpretation

This run separates three claims that should not be conflated:

1. **Historical association exists in some eras:** yes. Several direct calendar blocks strongly classify volatility in 2015-2020 and 2021-2026 after controlling for lagged volatility and Gregorian seasonality.
2. **The exact Chinese-calendar phase is uniquely informative:** not supported. Shifted versions are often stronger.
3. **The effect is stable enough to nominate a forward volatility rule:** no. Full-history and non-overlapping robustness fail, and important coefficients reverse sign across eras.

Therefore the project should not convert the late-era p-values into a trading rule or causal/metaphysical narrative.

## 10. Decision and next research direction

**Gate result: FAIL. No forward-only GANZHI_VOL_001 candidate is opened.**

The direct calendar-volatility branch is still methodologically useful because it explains the earlier natal-transit volatility anomaly: deterministic calendar/cycle states can synchronize with market volatility regimes without providing stable phase-specific predictive information.

The next useful research step is not to tune solar-term phases or choose the best historical day pillar. That would be post-hoc overfitting.

Instead, further branches should be genuinely different hypothesis generators with independently frozen rules and controls. Existing `ZIPING_FWD_001` remains the only active forward Ziping candidate and continues collecting post-2026-08-17 evidence without modification.
