# MetaAlpha Research Status

Snapshot date: **2026-08-17**

MetaAlpha tests deterministic Chinese symbolic-time systems as candidate market features under explicit falsification rules. This file is the current high-level evidence ledger; detailed protocols and audit artifacts remain in `registry/`, `reports/`, and `forward/`.

## 1. Current evidence hierarchy

| Branch / experiment | Evidence class | Current decision | Interpretation |
|---|---|---|---|
| Ziping v1-v4 standalone historical tests | historical exploration | mostly FAIL / no promotion | Increasing structural detail did not create stable next-session return evidence |
| `ZIPING_FWD_001` | prospective future-only | ACTIVE / secondary | Specific-rule follow-up; not an independent replication of the primary family |
| `GANZHI_VOL_001` | preregistered historical falsification | FAIL | Late-era volatility associations did not survive shifted/non-overlap/stability gates |
| `QIMEN_MARKET_001` | preregistered historical exploration | FAIL | No Qimen block passed the frozen market gate |
| `HYBRID_ALPHA_001 / cycle` | historical walk-forward OOS on selection market | PASS | Small incremental Shanghai Composite probability information historically |
| `HYBRID_ALPHA_001 / ziping` | historical walk-forward OOS on selection market | PASS | Small incremental Shanghai Composite probability information historically |
| `HYBRID_ALPHA_001 / qimen` | historical walk-forward OOS | FAIL | Only 2/4 outer windows improved |
| `HYBRID_ALPHA_001 / all_symbolic` | historical walk-forward OOS | FAIL | More symbolic complexity did not improve temporal stability |
| `HYBRID_REPL_001 / cycle` | external-index historical replication | **FAIL (0/4 indices)** | Historical Shanghai cycle result did not generalize across four new indices |
| `HYBRID_REPL_001 / ziping` | external-index historical replication | **FAIL (0/4 indices)** | Historical Shanghai Ziping result did not generalize across four new indices |
| `HYBRID_FWD_001` | prospective future-only | ACTIVE / shadow | Overlapping cycle/ziping shadow check; must not be counted as an independent replication |
| `META_FWD_001` | prospective future-only branch tournament | **ACTIVE / PRIMARY CONFIRMATORY** | baseline vs cycle / ziping / qimen / meihua, plus deterministic hash-six-line negative control |

The prospective evidence hierarchy is frozen in `registry/prospective_evidence_hierarchy.yaml`. A favorable secondary result cannot rescue a failure of the primary `META_FWD_001` family.

## 2. Strongest current falsification result

`HYBRID_REPL_001` applied the exact historically nominated `cycle` and `ziping` models to four markets without changing features, model family, tuning, outer windows, bootstrap, or gate:

- SSE 50
- CSI 300
- CSI 500
- Shenzhen Component

The preregistered replication threshold was at least 3/4 complete per-index gate passes.

Actual result:

- `cycle`: **0/4** complete gates passed;
- `ziping`: **0/4** complete gates passed.

Therefore the earlier Shanghai Composite `HYBRID_ALPHA_001` PASS must not be described as a general cross-index symbolic factor. The current defensible interpretation is:

> **Possible Shanghai-specific historical anomaly; no cross-index replication evidence.**

Detailed result: `reports/hybrid_replication_2026-08-16/RESULTS.md`.

## 3. Historical hybrid selection-market result

On 4,035 common Shanghai Composite OOS rows:

| Model | LogLoss | Brier | AUC | Historical gate |
|---|---:|---:|---:|---|
| baseline | 0.697251 | 0.251952 | 0.511733 | reference |
| cycle | 0.692099 | 0.249474 | 0.529573 | PASS |
| ziping | 0.692752 | 0.249789 | 0.525424 | PASS |
| qimen | 0.694649 | 0.250716 | 0.514141 | FAIL |
| all-symbolic | 0.693297 | 0.250032 | 0.529175 | FAIL |

Because the external-index replication subsequently failed, these PASS results are treated as model-selection evidence only.

Detailed result: `reports/hybrid_alpha_exploratory_2026-08-16/RESULTS.md`.

## 4. Prospective test A — `HYBRID_FWD_001`

Frozen start: **2026-08-17**.

Candidates:

- baseline
- cycle
- ziping

First immutable 2026-08-17 prediction was generated on 2026-08-16 before the 09:25 target-session anchor. Training market data ended on 2026-08-14.

First-record probabilities:

| Model | P(up) |
|---|---:|
| baseline | 0.540775 |
| cycle | 0.550974 |
| ziping | 0.555966 |

The first 500 eligible settled sessions are the one-time gate sample. The gate includes four chronological subwindows, effect-size thresholds, 20-session block bootstrap, and Holm family correction.

This experiment is now treated as an overlapping shadow check, not an independent replication of `META_FWD_001`.

## 5. Prospective test B — `META_FWD_001`

Frozen start: **2026-08-17**.

Finite candidate family:

1. cycle
2. ziping
3. qimen
4. `MEIHUA_TIME_V1`

Negative control:

- `LIUYAO_HASH_V1`: deterministic SHA-256 date-derived six-line state with no traditional interpretive claim.

No new candidate may be added to this family after the first eligible record.

### First immutable 2026-08-17 tournament record

Generated: **2026-08-16 22:15:40 Asia/Shanghai**  
Committed by GitHub Actions: **2026-08-16 22:16:45 Asia/Shanghai**  
Training data last date: **2026-08-14**  
Eligible before anchor: **yes**

| Model | P(up) | Status |
|---|---:|---|
| baseline | 0.540753 | reference |
| cycle | 0.551007 | candidate |
| ziping | 0.555977 | candidate |
| qimen | 0.523264 | candidate |
| meihua | 0.571606 | candidate |
| liuyao_hash | 0.529319 | negative control |

All six happen to be above 0.50 on the first record. This has no standalone evidentiary meaning.

### 2026-08-17 frozen symbolic states

Cycle:

- day pillar: `癸亥`
- previous solar term: `立秋`
- solar-term phase quartile: `2`
- month: `丙申`

Ziping:

- selected ten-god: `正印`
- selection mode: `primary_untransmitted_default`
- v3 route: `route_unresolved`

Qimen:

- `阴8 | 下元`
- duty star / door: `天冲 | 伤门`
- duty landings: star palace 2 / door palace 9

Meihua:

- base hexagram structural key: `离/乾`
- moving line: `1`
- changed key: `离/巽`
- mutual key: `兑/乾`
- body/use element relation: `体克用`

Hash-six-line negative control:

- base pattern: `011010`
- changed pattern: `011011`
- one moving line: line 6

### Tournament gate

At exactly the first 500 eligible settled sessions:

- each candidate must improve LogLoss in >=3/4 chronological subwindows;
- improve Brier in >=3/4;
- full-sample LogLoss improvement >=0.001;
- Brier improvement >=0.0005;
- AUC degradation no worse than 0.005;
- block-bootstrap probability of positive improvement >=0.95 for both primary losses;
- one-sided bootstrap p-values must survive Holm correction across the four candidate branches.

If multiple candidates pass, lowest locked-sample LogLoss is the descriptive winner.

If `LIUYAO_HASH_V1` passes the same core non-Holm candidate-like conditions, a **research alarm** is raised and no symbolic winner is promoted without separate review.

## 6. `MEIHUA_TIME_V1` frozen convention

The time-based Meihua engine was registered before market evaluation:

- lunar year earthly-branch ordinal: 子1 ... 亥12;
- lunar month and day numbers;
- leap month uses the corresponding absolute month number;
- fixed market anchor 09:25, therefore time branch is 巳=6;
- `(year + month + day) mod 8` -> upper trigram, zero -> 8;
- add time and mod 8 -> lower trigram, zero -> 8;
- total mod 6 -> moving line, zero -> 6;
- Earlier-Heaven order: 乾1兑2离3震4巽5坎6艮7坤8;
- trigram containing the moving line is `用`; the other is `体`;
- no numeric auspiciousness / fortune score is defined.

The frozen model uses only:

- base hexagram key
- moving line
- changed hexagram key
- mutual hexagram key
- body/use five-element relation

## 7. `META_FWD_001` reproducibility freeze

The forward family is now mechanically frozen at four layers.

### Predictor source

The predictive dependency closure is compared byte-for-byte against registration commit:

`12ddbcc66b0f1b3679c3f87ab1598cd538fdaa47`

Predictive feature engines, market preprocessing and model code may not drift under this family ID. Audit/reporting/settlement code may be repaired only if it does not alter the predictor closure.

### Runtime

The first eligible run is frozen to:

- CPython **3.11.15**;
- NumPy **2.4.6**;
- Pandas **3.0.5**;
- SciPy **1.17.1**;
- scikit-learn **1.9.0**;
- statsmodels **0.14.6**;
- lunar_python **1.4.8**;
- AKShare **1.18.84**;
- exact transitive versions in `requirements/meta-fwd-001.lock.txt`.

The lockfile itself is bound to SHA-256:

`f12b6780df99f96a7904d435c42344f5b809852dbff043d568306e7721ee2a8b`

### Prediction ledger

`forward/META_FWD_001/predictions/` is append-only. Every eligible record must:

- have exactly one exact-path Git commit touch;
- be committed before 09:25 on its target date;
- use training data strictly before the target date;
- match the frozen candidate/model/feature sets;
- pass independently recomputed eligibility checks.

The 2026-08-17 Sunday bootstrap is the sole grandfathered prior-civil-day record. After it, each prediction must be generated on the same Shanghai civil date as its target, preventing bulk early precommitment from bypassing the expanding-daily-refit rule.

### Realized-outcome ledger

`forward/META_FWD_001/realized/` is also append-only. A same-day result cannot be first locked before **15:30 Asia/Shanghai**. Each locked outcome stores previous trading close, target close, return, direction, source manifest and the SHA-256 of the matching prediction file.

Later vendor revisions cannot silently rewrite a previously locked confirmatory outcome.

Detailed reproducibility policy: `registry/meta_fwd_001_reproducibility.yaml`.

## 8. Current stop rules

The following are prohibited under existing hypothesis IDs:

- dropping failed external replication indices;
- retrospectively deleting losing symbolic features;
- switching to a nonlinear rescue model after seeing results;
- weakening temporal-stability or multiple-testing gates;
- reinterpreting a failed branch as successful by selecting a convenient era;
- adding new `META_FWD_001` candidates after its first record;
- changing predictor-source bytes under `META_FWD_001`;
- changing the first-run Python/package environment under `META_FWD_001`;
- bulk-generating future target dates instead of same-day expanding refits;
- overwriting an existing prediction or realized outcome;
- counting `HYBRID_FWD_001`, `ZIPING_FWD_001` and `META_FWD_001` as independent replications;
- using the negative-control result as a tradable model.

Any genuinely new predictive formulation now requires a **new hypothesis/family ID before its first inspected outcome**.

## 9. Engineering freeze checkpoint

As of the 2026-08-17 pre-market checkpoint, CI has passed all of the following on the frozen runtime:

- predictor-source byte freeze;
- runtime/package freeze;
- full pytest suite, including anti-leakage, immutable-ledger and daily-refit tests;
- immutable prediction-ledger audit;
- immutable realized-ledger audit.

The experiment mechanics are therefore **frozen for evidence collection**. Further work under `META_FWD_001` should be limited to non-predictive operational repairs required to preserve the registered protocol. No such repair may alter already committed probabilities, candidate definitions, gate thresholds or locked outcomes.

## 10. What matters next

The project has reached the point where more historical searching or predictor engineering would reduce rather than increase evidentiary credibility.

The next informative observations are external:

1. the 08:10 scheduled job verifies the frozen environment/source and refuses to overwrite the already committed 2026-08-17 prediction;
2. the market session supplies the first unseen outcome;
3. after 15:30, and operationally at the 16:40 scheduled settlement, the first realized outcome can be locked to the immutable ledger;
4. the process repeats under the same-day expanding-refit rule until the first 500 eligible settled sessions are complete.

Daily leaders remain descriptive only. The first-day result, whether correct or incorrect, cannot promote or kill a branch by itself.
