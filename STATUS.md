# MetaAlpha Research Status

Snapshot date: **2026-08-16**

MetaAlpha tests deterministic Chinese symbolic-time systems as candidate market features under explicit falsification rules. This file is the current high-level evidence ledger; detailed protocols and audit artifacts remain in `registry/`, `reports/`, and `forward/`.

## 1. Current evidence hierarchy

| Branch / experiment | Evidence class | Current decision | Interpretation |
|---|---|---|---|
| Ziping v1-v4 standalone historical tests | historical exploration | mostly FAIL / no promotion | Increasing structural detail did not create stable next-session return evidence |
| `ZIPING_FWD_001` | prospective future-only | ACTIVE | Tests the frozen historical `偏财` candidate from 2026-08-17 onward |
| `GANZHI_VOL_001` | preregistered historical falsification | FAIL | Late-era volatility associations did not survive shifted/non-overlap/stability gates |
| `QIMEN_MARKET_001` | preregistered historical exploration | FAIL | No Qimen block passed the frozen market gate |
| `HYBRID_ALPHA_001 / cycle` | historical walk-forward OOS on selection market | PASS | Small incremental Shanghai Composite probability information historically |
| `HYBRID_ALPHA_001 / ziping` | historical walk-forward OOS on selection market | PASS | Small incremental Shanghai Composite probability information historically |
| `HYBRID_ALPHA_001 / qimen` | historical walk-forward OOS | FAIL | Only 2/4 outer windows improved |
| `HYBRID_ALPHA_001 / all_symbolic` | historical walk-forward OOS | FAIL | More symbolic complexity did not improve temporal stability |
| `HYBRID_REPL_001 / cycle` | external-index historical replication | **FAIL (0/4 indices)** | Historical Shanghai cycle result did not generalize across four new indices |
| `HYBRID_REPL_001 / ziping` | external-index historical replication | **FAIL (0/4 indices)** | Historical Shanghai Ziping result did not generalize across four new indices |
| `HYBRID_FWD_001` | prospective future-only | ACTIVE | Frozen Shanghai baseline vs cycle vs ziping; first 500 eligible sessions form immutable gate sample |
| `META_FWD_001` | prospective future-only branch tournament | ACTIVE | baseline vs cycle / ziping / qimen / meihua, plus deterministic hash-six-line negative control |

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

No result before that gate is confirmatory.

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

## 7. Current stop rules

The following are prohibited under existing hypothesis IDs:

- dropping failed external replication indices;
- retrospectively deleting losing symbolic features;
- switching to a nonlinear rescue model after seeing results;
- weakening temporal-stability or multiple-testing gates;
- reinterpreting a failed branch as successful by selecting a convenient era;
- adding new `META_FWD_001` candidates after its first record;
- using the negative-control result as a tradable model.

## 8. What matters next

The project has reached the point where **more historical searching has sharply diminishing evidentiary value**.

The highest-value evidence now comes from immutable future records:

- `ZIPING_FWD_001`
- `HYBRID_FWD_001`
- `META_FWD_001`

Historical work should be limited to engineering QC, independent source validation, and explicitly new hypotheses that receive new IDs before their outcomes are inspected.
