# ZIPING_V4_001 — Corrected Structural Predicate Historical Results

Run date: 2026-08-16  
Corrected workflow run: `31946412286`  
Commit evaluated: `14e0a5316bac3cfb1afa7eec32b6d0e3018bdc8b`  
Corrected artifact ID: `9263411125`  
Artifact ZIP SHA256: `4843bb5e492fecc89c186cf529ddea6a71c94380dd132e6aaca2c260a5566513`

Superseded initial run: `31946158306` — **INVALIDATED FOR INFERENTIAL USE**. See `INITIAL_RUN_INVALIDATION.md`.

## 1. Executive decision

**ZIPING_V4_001 FAILS its preregistered historical-interest gate.**

No v4 forward market experiment is opened.

After correcting the inferential QC bug, no valid registered v4 structural feature passes 0.05 family BH-FDR in any descriptive era or in the full historical sample. The source-defined 财印 position refinement also fails to reproduce the earlier v3 unresolved-position anomaly.

A preregistered shifted-session control is substantially stronger than the real v4 features in 2021-2026, further weakening any claim that the registered structural states carry unique next-session-return information.

## 2. Data and frozen model

- market: Shanghai Composite `000001`;
- source: pinned Sina via `ak.stock_zh_index_daily`;
- AKShare version: `1.18.84`;
- sessions: `8,704`;
- first session: `1990-12-19`;
- last session: `2026-08-14`;
- canonical normalized-data SHA256: `697af81a200060d42b04fa7a79b92fb8287e709ae10baf0825ae301fb4af5aa1`;
- target: next-session return (`ret_fwd_1`);
- baseline fixed effects: v2 selected-use ten god, v3 route state, Gregorian weekday and Gregorian month;
- inference: OLS with Newey-West/HAC covariance, `maxlags=5`;
- registered v4 features: source-defined position, exact rooting, raw support/drain profiles and refined route completion states;
- rare levels: fewer than 100 era observations collapse to `__RARE__`;
- multiple testing: Benjamini-Hochberg across valid registered features within each era;
- nulls: each registered v4 feature shifted by 17/31/47 dataset sessions under the same frozen baseline;
- no numeric strength or fortune score is defined.

## 3. Inference-QC correction

The first v4 run exposed structural collinearity in `zpzt_route__v4__route_state`: the frozen baseline already contains v3 route-state fixed effects, while v4 route state is a deterministic refinement of v3 state.

The corrected runner requires:

1. full column rank of the complete design matrix;
2. full rank of the HAC covariance submatrix for the tested dummy block.

A failed condition creates an audit row with `valid_inference=0` and no usable p-value. Invalid tests do not enter BH-FDR and do not contribute coefficient maxima.

Exactly five registered tests are invalidated: `zpzt_route__v4__route_state` once in each descriptive/full-history era. All five fail because the design matrix is rank deficient. No shifted-control test is invalidated.

## 4. Corrected family-level results

| Era | Valid registered tests | Invalid registered tests | Registered min BH-FDR | Shift-null min BH-FDR | Max valid registered incremental R² |
|---|---:|---:|---:|---:|---:|
| 1990-2004 | 10 | 1 | 0.184619 | 0.242556 | 0.004120 |
| 2005-2014 | 10 | 1 | 0.899826 | 0.356731 | 0.003298 |
| 2015-2020 | 10 | 1 | 0.903802 | 0.890136 | 0.001841 |
| 2021-2026 | 10 | 1 | 0.992981 | **0.000042146** | 0.001418 |
| Full history | 10 | 1 | 0.195903 | 0.358858 | 0.001893 |

No valid registered v4 family passes the 0.05 threshold.

## 5. Best valid registered observations

These are descriptive only and do not pass family correction.

### 1990-2004

Best feature: `zpzt_structure__v4__daymaster_root_bin`

- raw p: `0.018462`;
- family BH-FDR: `0.184619`;
- incremental R²: `0.001525`;
- largest absolute dummy coefficient: about `33.42 bp`.

### 2005-2014

Best feature: `zpzt_route__v4__route_blocked_count`

- raw p: `0.116666`;
- family BH-FDR: `0.899826`;
- incremental R²: `0.001141`.

### 2015-2020

Best feature: `zpzt_structure__v4__daymaster_root_bin`

- raw p: `0.281927`;
- family BH-FDR: `0.903802`.

### 2021-2026

Best feature: `zpzt_structure__v4__daymaster_root_month`

- raw p: `0.223585`;
- family BH-FDR: `0.992981`.

### Full history

Best feature: `zpzt_structure__v4__daymaster_root_bin`

- raw p: `0.019590`;
- family BH-FDR: `0.195903`;
- incremental R²: `0.000632`.

The recurring low raw p-value for day-master root bins does not survive family correction and does not strengthen in later eras.

## 6. The v3 position anomaly does not survive source-defined resolution

V3 had one family-significant historical anomaly in 2005-2014: the coarse `requires_position_route_count` feature had family BH-FDR approximately `0.0286` and a level coefficient near `-41.7 bp`.

V4 replaced that unresolved bucket with source-defined position evidence for 财格佩印:

- `position_condition_satisfied`: visible wealth/resource components are separated;
- `position_condition_blocked`: visible wealth/resource components are directly adjacent;
- `position_condition_ambiguous_multiple`: both adjacent and separated pairs exist;
- `not_applicable`: both visible families are not present.

In 2005-2014:

- `wealth_resource_position_resolution`: raw p ≈ `0.800`;
- `resolved_from_position_count`: raw p ≈ `0.380`;
- `route_blocked_count`: raw p ≈ `0.1167`.

Thus the earlier v3 association does not become stronger when the unresolved classical position condition is made more source-faithful. It disappears.

**Interpretation:** the v3 result should not be treated as evidence for the classical 财印 position rule. It was an era-specific association attached to a coarse unresolved-state bucket.

## 7. Shifted-control failure

The strongest corrected v4 result is not a registered feature at all. It is the 47-session shifted version of `zpzt_route__v4__route_blocked_count` in 2021-2026:

- raw HAC joint p ≈ `1.28e-6`;
- shift-family BH-FDR ≈ `4.2146e-5`;
- incremental R² ≈ `0.002545`;
- the eligible rare-state dummy coefficient is approximately `-64.49 bp`;
- t-statistic ≈ `-4.84`.

The real, unshifted `route_blocked_count` in the same era is not significant after correction.

This is exactly the type of null-control behavior that the research framework is designed to surface. A displaced deterministic calendar state can look stronger than the purported source-faithful state.

## 8. Preregistered gate

The gate required the same valid registered v4 feature to survive 0.05 family correction in at least two of:

- 2005-2014;
- 2015-2020;
- 2021-2026;

while not being materially weaker than its shifted controls.

No registered v4 feature survives even one of those later eras.

**Gate result: FAIL.**

## 9. Research decision

The project should not continue adding increasingly detailed single-session Ziping return features merely to search for another historical anomaly.

The source-faithful sequence now provides a meaningful falsification trail:

1. v1 month-primary/state features did not produce stable return evidence;
2. v2 month-use change materially improved the classical representation but did not yield an independent stable return factor;
3. v3 assistant/formation routes failed cross-era replication;
4. v4 source-defined position/root/support predicates fail after stricter incremental controls, and the one earlier position anomaly disappears after refinement.

The existing forward-only `ZIPING_FWD_001` remains valid because it was frozen separately before future outcomes. It should continue collecting genuine post-2026-08-17 observations without rule changes.

Further historical development effort should move away from single-session Ziping next-return prediction and toward directly testable deterministic calendar/Ganzhi/solar-term regime questions, especially volatility, with Gregorian seasonality and shifted/random controls explicitly included.
