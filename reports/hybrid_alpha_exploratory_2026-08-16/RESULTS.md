# HYBRID_ALPHA_001 — Incremental Symbolic-State OOS Results

Run date: 2026-08-16  
Workflow run: `31950483358`  
Commit evaluated: `cc05302dccf9a94676f1b97ffe1430ce4156ad63`  
Artifact ID: `9264515028`  
Artifact ZIP SHA256: `3f621382f56f6538b37d7490ad8d47eb697a97cee87baf4a3f4cf58e38eb47d2`

## 1. Evidence status

**EXPLORATORY WALK-FORWARD OOS OVER PRE-EXISTING HISTORY.**

The protocol, feature lists, model family, hyperparameter grid, outer windows, bootstrap and acceptance gate were frozen before this first run. However, the underlying historical market outcomes and several symbolic feature families had already been studied in earlier MetaAlpha experiments. This run is therefore useful model-selection evidence, but it is not a pristine future holdout and cannot by itself establish a tradable effect.

## 2. Executive decision

Two preregistered symbolic blocks pass the complete `HYBRID_ALPHA_001` historical-interest gate:

- **PASS — `cycle`**
- **PASS — `ziping`**

Two blocks fail:

- **FAIL — `qimen`**
- **FAIL — `all_symbolic`**

Only the frozen `cycle` and `ziping` representations qualify for separately registered future-only evaluation. No historical feature deletion, interaction search, nonlinear rescue model, or threshold retuning is permitted under `HYBRID_ALPHA_001`.

The important qualitative result is that the union of all symbolic systems does **not** outperform the more constrained winners consistently enough to pass. More symbolic complexity is therefore not treated as evidence of greater predictive value.

## 3. Data and information boundary

- market: Shanghai Composite `000001`;
- provider: pinned Sina via `ak.stock_zh_index_daily`;
- AKShare version: `1.18.84`;
- first session: `1990-12-19`;
- last session: `2026-08-14`;
- raw observations: `8,704`;
- common eligible rows after all frozen feature requirements: `8,683`;
- common OOS prediction rows: `4,035`;
- canonical normalized-data SHA256: `697af81a200060d42b04fa7a79b92fb8287e709ae10baf0825ae301fb4af5aa1`;
- prediction anchor: `09:25 Asia/Shanghai`;
- target: same-session close-to-close direction;
- every ordinary market predictor is available no later than `t-1` close;
- symbolic predictors are deterministic states for `t` at 09:25;
- no same-session OHLCV or return is used as a predictor.

## 4. Frozen baseline

The conventional market baseline contains only lagged information:

- 1/2/5/10/20-session trailing returns;
- previous-session absolute return;
- lagged 5/20-session realized volatility;
- previous-session overnight gap;
- previous-session high-low range;
- lagged close distance from 5/20-session moving averages;
- lagged 20-session drawdown;
- lagged log-volume change;
- lagged 20-session volume z-score;
- normalized secular time and squared time;
- Gregorian weekday and month.

The primary model is L2-regularized logistic regression with one-hot categorical encoding and time-ordered inner tuning over `C = {0.01, 0.1, 1, 10}`.

## 5. Frozen outer walk-forward

Expanding training samples were evaluated on four non-overlapping OOS eras:

1. 2010-2013 — 967 rows
2. 2014-2017 — 977 rows
3. 2018-2021 — 973 rows
4. 2022-2026-08-14 — 1,118 rows

A one-session train/test embargo was applied.

## 6. Full-OOS metrics

| Model | LogLoss | Brier | ROC AUC | Accuracy | Calibration slope | High-low probability bucket return spread |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 0.697251 | 0.251952 | 0.511733 | 0.522429 | 0.225154 | 0.000540 |
| **cycle** | **0.692099** | **0.249474** | **0.529573** | **0.530607** | 0.600567 | **0.001593** |
| qimen | 0.694649 | 0.250716 | 0.514141 | 0.524411 | 0.290071 | 0.000064 |
| **ziping** | **0.692752** | **0.249789** | **0.525424** | 0.523172 | 0.525938 | **0.001135** |
| all_symbolic | 0.693297 | 0.250032 | 0.529175 | 0.530607 | 0.467614 | 0.001064 |

The baseline itself is weak, as expected for same-session index direction prediction. The experiment is therefore about **incremental probabilistic information**, not a claim that any model has strong standalone market-timing accuracy.

## 7. Incremental results versus identical baseline OOS rows

| Block | LogLoss improvement | Brier improvement | AUC delta | LogLoss windows won | Brier windows won | Bootstrap P(improve), LogLoss | Bootstrap P(improve), Brier | Holm p, LogLoss | Holm p, Brier | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **cycle** | **+0.005152** | **+0.002478** | **+0.017840** | **3/4** | **3/4** | **1.0000** | **1.0000** | **0.0000** | **0.0000** | **PASS** |
| qimen | +0.002602 | +0.001236 | +0.002408 | 2/4 | 2/4 | 0.9935 | 0.9860 | 0.0065 | 0.0140 | FAIL |
| **ziping** | **+0.004498** | **+0.002164** | **+0.013691** | **3/4** | **3/4** | **1.0000** | **1.0000** | **0.0000** | **0.0000** | **PASS** |
| all_symbolic | +0.003953 | +0.001921 | +0.017442 | 2/4 | 2/4 | 0.9970 | 0.9970 | 0.0060 | 0.0060 | FAIL |

The 20-session block-bootstrap 95% intervals for the mean loss improvements were strictly above zero for all four blocks, but the frozen gate also required temporal repetition in at least three of four outer windows. This is why `qimen` and `all_symbolic` correctly fail despite favorable aggregate statistics.

## 8. Era-by-era behavior

### 2010-2013

Baseline LogLoss: `0.717801`

- cycle: `0.700033` — improves
- qimen: `0.702082` — improves
- ziping: `0.700803` — improves
- all_symbolic: `0.701544` — improves

### 2014-2017

Baseline LogLoss: `0.684356`

- cycle: `0.684645` — slightly worse
- qimen: `0.685236` — worse
- ziping: `0.683433` — improves
- all_symbolic: `0.684737` — worse

### 2018-2021

Baseline LogLoss: `0.693673`

- cycle: `0.691916` — improves
- qimen: `0.697977` — materially worse
- ziping: `0.692701` — improves
- all_symbolic: `0.695062` — worse

### 2022-2026-08-14

Baseline LogLoss: `0.693858`

- cycle: `0.691910` — improves
- qimen: `0.693548` — improves slightly
- ziping: `0.693977` — slightly worse
- all_symbolic: `0.692109` — improves

This is why `cycle` and `ziping` each reach the required 3/4 repetition, while `qimen` and `all_symbolic` do not.

## 9. Selected regularization strengths

Inner expanding-time validation selected strong regularization for nearly all augmented models:

| Window | baseline C | cycle C | qimen C | ziping C | all-symbolic C |
|---|---:|---:|---:|---:|---:|
| 2010-2013 | 0.1 | 0.01 | 0.01 | 0.01 | 0.01 |
| 2014-2017 | 0.1 | 0.01 | 0.01 | 0.01 | 0.01 |
| 2018-2021 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 |
| 2022-2026 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 |

This is consistent with a weak-signal, high-dimensional categorical setting and argues against using a more flexible nonlinear model as a post-hoc rescue mechanism.

## 10. Interpretation

The strongest defensible statement is:

> Under the preregistered ridge-logistic representation, deterministic Chinese calendar-cycle features and the frozen Ziping structural feature block contain a small but repeatable amount of incremental probabilistic information relative to a lagged-market baseline across the historical walk-forward test.

This result does **not** establish:

- metaphysical causality;
- a profitable trading strategy after costs;
- robustness to other indices or individual stocks;
- robustness to alternative market-feature baselines;
- a pristine unseen future result;
- superiority of all traditional systems collectively.

In particular, `all_symbolic` failing while `cycle` and `ziping` pass is evidence against indiscriminately stacking every symbolic system.

## 11. Decision

- `cycle`: **HISTORICAL_GATE_PASS — PROMOTE TO FROZEN FUTURE-ONLY TEST**
- `ziping`: **HISTORICAL_GATE_PASS — PROMOTE TO FROZEN FUTURE-ONLY TEST**
- `qimen`: **HISTORICAL_GATE_FAIL — NO FUTURE PROMOTION FROM THIS RUN**
- `all_symbolic`: **HISTORICAL_GATE_FAIL — NO FUTURE PROMOTION FROM THIS RUN**

The future-only tests must retain the exact feature definitions and ridge-logistic modeling family used here. Historical results may not be used to delete features, add interactions, change Qimen conventions, change Ziping rules, or tune a new acceptance threshold.
