# ZIPING_V2_001 — Month-Use Change Historical Exploration Results

Run date: 2026-08-16  
Workflow run: `31945146914`  
Commit evaluated: `730e81c6fb2bc7c7d275310f9bf9afd59351bb46`  
Artifact ID: `9263074523`  
Artifact ZIP SHA256: `b741cd2733f26d6542c4fb5c5f7e6bb22d80de02a9dbed5aa346a9b5a5e2e284`

## 1. Evidence status

**Exploratory only.** All observations through 2026-08-14 were already exposed at project level before this family was evaluated. No historical result in this report is confirmatory evidence.

The v2 family adds source-constrained month-use-change primitives for:

- month-command hidden-stem transmission;
- primary versus secondary transmitted use;
- complete three-harmony transformations involving the month branch;
- single versus multiple visible use components;
- mixed broad ten-god families.

No numerical strength or fortune score is defined.

## 2. Data and inference

- market: Shanghai Composite `000001`;
- provider: pinned Sina via `ak.stock_zh_index_daily`;
- AKShare version: `1.18.84`;
- sessions: `8,704`;
- first session: `1990-12-19`;
- last session: `2026-08-14`;
- canonical normalized-data SHA256: `697af81a200060d42b04fa7a79b92fb8287e709ae10baf0825ae301fb4af5aa1`;
- target: next-session return (`ret_fwd_1`);
- inference: one-vs-rest OLS with Newey-West/HAC covariance, `maxlags=5`;
- multiple testing: Benjamini-Hochberg across the complete registered v2 family within each era/test class;
- controls: 17/31/47-session shifted versions of every registered v2 feature, plus Gregorian weekday/month baseline;
- each descriptive era purges its last session so its next-session target cannot cross the era boundary.

## 3. How often v2 actually changes v1

The v2 layer is not a column rename. Across 8,704 sessions:

- `use_change_detected=1`: `2,312` sessions (`26.56%`);
- `secondary_transmitted`: `2,219` sessions;
- `primary_transmitted`: `2,667` sessions;
- `primary_untransmitted_default`: `3,818` sessions;
- complete month-involving three-harmony state: `295` sessions;
- mixed broad use families: `1,097` sessions.

Composition modes:

| Mode | Sessions |
|---|---:|
| default_primary_only | 3,713 |
| single_transmitted | 3,713 |
| multiple_transmitted | 983 |
| transmission_plus_harmony | 190 |
| harmony_only | 105 |

Thus the v2 engine materially changes the operational state on roughly one quarter of sessions while remaining deterministic.

## 4. Family-level results

Minimum family BH-FDR:

| Era | Registered v2 | Shift null | Gregorian baseline |
|---|---:|---:|---:|
| 1990-2004 | 0.1840 | 0.2822 | 0.1543 |
| 2005-2014 | 0.5152 | 0.6794 | 0.2129 |
| 2015-2020 | 0.05581 | 0.7286 | 0.4039 |
| 2021-2026 | 0.03011 | 0.9948 | 0.6844 |
| full history | 0.2292 | 0.1222 | 0.3301 |

The registered family does not show a universal full-history effect. Its strongest behavior is concentrated in later eras rather than appearing mechanically across the entire sample.

## 5. The 2015-2020 near-threshold result

The leading registered state was `zpzt_use__v2__use_change_detected`:

- changed-use state (`1`): `n=417`, mean next-session return `+0.1838%`;
- unchanged state (`0`): `n=1,044`, mean `-0.0548%`;
- mean difference: approximately `+23.85 bp`;
- standardized effect: `+0.1627`;
- raw HAC p-value: `0.00372`;
- family BH-FDR: `0.05581`.

This is close to but does not pass the registered 0.05 family-FDR threshold.

More importantly, the same `use_change_detected=1` state is **negative** in 2021-2026. Therefore the generic claim that “用神发生变化 predicts positive next-session return” fails the directional-stability requirement and is not nominated for a forward test.

## 6. The 2021-2026 significant result

The family passes 0.05 BH-FDR in the already-exposed 2021-2026 era. The leading levels are:

### Selected 偏财

- `n=147`;
- mean next-session return: `+0.2684%`;
- rest mean: `-0.0176%`;
- difference: `+28.60 bp`;
- standardized effect: `+0.2887`;
- raw HAC p-value: `0.00135`;
- family BH-FDR: `0.03011`.

### Selected 正财

- `n=147`;
- mean next-session return: `-0.1972%`;
- rest mean: `+0.0388%`;
- difference: `-23.60 bp`;
- standardized effect: `-0.2383`;
- raw HAC p-value: `0.00201`;
- family BH-FDR: `0.03011`.

The shifted-null family in the same era has minimum BH-FDR `0.9948`, so this particular late-era anomaly is not reproduced by the registered 17/31/47-session displacements.

However, this is not independent confirmation. It is closely related to the previously exposed v1 wealth-polarity anomaly and is observed in the same already-burned market era.

## 7. Cross-era sign stability

Several selected-use levels have stable signs even though most individual eras are not significant after family correction:

### Selected 正财

The effect is negative in all four descriptive eras:

| Era | Mean difference | Standardized effect | Family BH-FDR |
|---|---:|---:|---:|
| 1990-2004 | -12.17 bp | -0.0390 | 0.6171 |
| 2005-2014 | -17.36 bp | -0.1039 | 0.5392 |
| 2015-2020 | -21.54 bp | -0.1469 | 0.4657 |
| 2021-2026 | -23.60 bp | -0.2383 | 0.03011 |

### Selected 正官

The effect is positive in all four descriptive eras:

| Era | Mean difference | Standardized effect | Family BH-FDR |
|---|---:|---:|---:|
| 1990-2004 | +9.83 bp | +0.0315 | 0.6171 |
| 2005-2014 | +21.12 bp | +0.1264 | 0.5152 |
| 2015-2020 | +14.66 bp | +0.1000 | 0.4657 |
| 2021-2026 | +10.20 bp | +0.1030 | 0.5292 |

### Selected 偏财

The effect is negative in 1990-2004 but positive in each later era. It therefore does not satisfy four-era sign stability.

## 8. Decision

**Decision: v2 is structurally meaningful, but ZIPING_V2_001 does not establish an independent robust return factor.**

The v2 operationalization changes approximately 26.6% of sessions and correctly distinguishes source-defined transmission/harmony states. That is a methodological improvement over pinning the month primary qi as the only possible use.

Statistically, however:

1. the full-history registered family does not pass the 0.05 gate;
2. the generic `use_change_detected` signal reverses direction between 2015-2020 and 2021-2026;
3. the 2021-2026 significance is dominated by the same broad wealth-polarity phenomenon already exposed in v1;
4. stable-sign 正财/正官 levels remain mostly weak after family correction outside the latest era.

Therefore this run does **not** justify opening a second forward test merely because one late historical era is significant.

## 9. Next research step

The next source-faithful layer should model **相神 and route-dependent 成败救应**, not add another scalar five-element score.

The implementation should record:

- the selected/changed month use;
- which auxiliary ten-god route actually supports that use;
- which control/transform route handles an adverse use;
- whether the auxiliary route is present in visible stems or completed branch structures;
- whether an auxiliary stem is mechanically combined/neutralized;
- which formation rules remain unresolved because they explicitly require strength, rooting or position conditions.

This should be a new versioned feature family. Existing v1/v2 historical results must not be rewritten after the fact.
