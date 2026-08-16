# ZIPING_V3_001 — Incremental Assistant/Route Graph Historical Results

Run date: 2026-08-16  
Workflow run: `31945754655`  
Commit evaluated: `6034e6859d9641880bbebbe98aad613d24cabd28`  
Artifact ID: `9263232204`  
Artifact ZIP SHA256: `a6603b90c08fdbe69012767aeb8f992b8bceaec3c60ddc27ee24bbec3e255e59`

## 1. Evidence status

**Exploratory only.** All Shanghai Composite observations through 2026-08-14 were already exposed at project level. This run cannot confirm a market hypothesis.

The v3 layer asks a narrower question than v1/v2:

> After controlling for the v2 selected-use ten god and ordinary Gregorian weekday/month seasonality, do source-constrained 相神 / 成格 / 救应 route states add incremental next-session-return information?

The answer from this historical run is **no robust cross-era incremental candidate**.

## 2. Method

- market: Shanghai Composite `000001`;
- source: pinned Sina via `ak.stock_zh_index_daily`;
- AKShare version: `1.18.84`;
- rows: `8,704`;
- first session: `1990-12-19`;
- last session: `2026-08-14`;
- normalized-data SHA256: `697af81a200060d42b04fa7a79b92fb8287e709ae10baf0825ae301fb4af5aa1`;
- target: `ret_fwd_1`;
- baseline fixed effects: v2 selected-use ten god, Gregorian weekday, Gregorian month;
- inference: OLS with Newey-West/HAC covariance, `maxlags=5`;
- route feature test: joint Wald test across the categorical route-feature dummy block;
- rare levels: levels with fewer than 100 era observations collapse into `__RARE__`;
- multiple testing: Benjamini-Hochberg across the 9 registered route features in each era;
- nulls: identical models using each route feature shifted by 17/31/47 dataset sessions;
- each era purges its final session so a next-session label cannot cross its boundary.

All fitted registered designs were full rank; no registered era test was marked rank-deficient.

## 3. Family-level diagnostic minima

| Era | Registered min BH-FDR | Shift-null min BH-FDR | Max registered incremental R² |
|---|---:|---:|---:|
| 1990-2004 | 0.1550 | 0.05778 | 0.001163 |
| 2005-2014 | **0.02863** | 0.76350 | 0.003292 |
| 2015-2020 | 0.45392 | 0.58730 | 0.003456 |
| 2021-2026 | 0.63775 | 0.91213 | 0.002346 |
| Full history | 0.58640 | 0.46290 | 0.000416 |

There is no full-history route-family significance and no later-era repetition of the one 2005-2014 result.

## 4. The sole family-significant registered result

The only registered route feature passing 0.05 family BH-FDR was:

`zpzt_route__v3__requires_position_route_count`

in 2005-2014.

Results:

- raw HAC joint p-value: `0.003181`;
- family BH-FDR: `0.028628`;
- incremental R² above the frozen baseline: `0.003292`;
- route level `1` coefficient relative to level `0`: approximately `-41.74 bp` per next session;
- t-statistic: approximately `-2.95`.

The preregistered shifted controls for the same source feature did not reproduce it:

| Shift | Raw p-value | Shift-family BH-FDR | Max absolute beta |
|---:|---:|---:|---:|
| 17 sessions | 0.25984 | 0.76350 | 14.53 bp |
| 31 sessions | 0.57569 | 0.86354 | 6.51 bp |
| 47 sessions | 0.32616 | 0.76350 | 10.71 bp |

This makes the 2005-2014 observation more interesting than a simple displaced-calendar artifact, but it is still insufficient under the frozen cross-era gate.

## 5. Why this is not a usable 相神 signal

`requires_position_route_count` does **not** mean that a favorable assistant has been fully established. It marks the presence of a registered classical route whose correctness depends on an unresolved positional condition.

In v3 the principal example is the 财格 + 印 route: the source condition depends on the relevant components being positioned so that they do not directly damage one another. V3 deliberately records that condition as unresolved instead of inventing a scalar rule.

Therefore the negative 2005-2014 coefficient cannot be translated into a claim such as “相神 is bearish.” It only says that this unresolved structural state happened to carry incremental return association in one historical era.

## 6. Cross-era gate

The preregistered exploratory-interest gate required the **same registered route feature** to survive family correction in at least two of:

- 2005-2014;
- 2015-2020;
- 2021-2026;

and not be materially weaker than its shifted controls.

No route feature satisfies that requirement.

`requires_position_route_count` passes only in 2005-2014. Its later-era family-adjusted evidence is not significant.

## 7. Other observations

- 1990-2004 `source_example_rescue_hit_count` has raw p ≈ `0.0172`, but family BH-FDR ≈ `0.155`; it does not survive multiplicity correction.
- 2015-2020 and 2021-2026 contain no family-significant registered route feature.
- Full-history registered minimum BH-FDR is approximately `0.586`, so v3 does not create an all-period route anomaly after controlling for v2 selected use and Gregorian calendar effects.
- Incremental R² values are small throughout, with the largest registered era value below `0.0035`.

## 8. Decision

**ZIPING_V3_001 fails its preregistered historical-interest gate.**

No v3 forward market experiment is opened from this run.

This does not imply that every classical 相神/成败 formulation is false. It means the currently source-constrained v3 route graph, with unresolved strength/quantity/position conditions left explicitly unresolved, does not show sufficiently stable incremental next-session-return information to justify promotion.

## 9. Next methodological step

Further development should target the unresolved classical predicates themselves rather than adding more generic route labels or arbitrary weights:

1. **position** — explicit stem positions and whether two relevant visible stems are adjacent/separated, plus whether a required combination directly links them;
2. **rooting** — exact visible-stem rooting in the four branches and whether the root is month/day/year/time;
3. **quantity** — counts of exact supporting/opposing visible and hidden components, kept as raw primitives rather than a tuned total score;
4. **strength dependence** — categorical, preregistered structural states built from month relation + exact roots + support/drain counts, with no fitted coefficients used to define the state;
5. only then re-evaluate route completion as a new versioned feature family.

Historical data remain exploratory. Any promoted rule still requires a separately frozen forward-only test.
