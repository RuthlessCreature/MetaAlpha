# RFC-0001: MetaAlpha v0.1

## 1. Background

Traditional Chinese temporal-symbolic systems such as Ganzhi, Wuxing, Bazi, Qimen and Yijing are often used informally to describe market timing. Those claims are usually impossible to audit because the rule is not frozen before testing, the feature definition is discretionary, and failed variants disappear from memory.

MetaAlpha converts those claims into preregistered, deterministic, machine-readable hypotheses and evaluates them with modern statistical validation.

## 2. Goal

Build a reproducible research system that can answer three questions:

1. Does a symbolic/calendar feature have marginal predictive information?
2. Does a relational rule add information beyond raw labels?
3. Does the feature family add out-of-sample information beyond ordinary calendar and market variables?

## 3. Non-goals

- Proving metaphysical causality.
- Producing discretionary fortune-telling narratives.
- Publishing buy/sell recommendations in v0.1.
- Optimizing on the sealed holdout.
- Retrofitting rule definitions after seeing results.

## 4. Research branches

### C0 — Controls
Gregorian calendar, randomized labels, shifted-date features and fake-birth-date controls.

### C1 — Ganzhi
Year/month/day stems and branches, 60-Jiazi identifiers, yin/yang mappings.

### C2 — Wuxing and solar terms
Element mappings, 24 solar terms, deterministic aggregate element-state features.

### C3 — Bazi relational layer
A stable interface for original-chart versus transit relations: generation, control, combinations, clashes, punishments, harms and breaks. This branch must never rely on free-form LLM interpretation.

### C4+ — Later
Qimen, Meihua, Yijing and Liuyao. Each school or calendrical convention is versioned as an independent hypothesis family.

## 5. Units of observation

### Market timing
One row per trading session per instrument/index.

### Cross-sectional
One row per stock per trading session.

## 6. Required base columns

```text
symbol
date
open
high
low
close
volume
```

Optional market data may include turnover, amount, free-float market cap, industry, limit-up/down state and breadth variables.

## 7. Feature contract

Every feature engine must be:

- deterministic for identical inputs;
- versioned;
- free of future information;
- serializable to tabular columns;
- independently testable;
- accompanied by a documented calendar/time convention.

Feature names use:

```text
<branch>__<version>__<feature>
```

Example:

```text
ganzhi__v1__weekday
ganzhi__v1__day_stem
control__v1__shift_17_day_branch
```

## 8. Time convention

All market-session features are computed using Asia/Shanghai civil time unless a registered hypothesis explicitly defines otherwise. A feature requiring session-close information cannot be used to predict the same session.

## 9. Labels

For close prices C_t:

```text
ret_fwd_1 = C[t+1] / C[t] - 1
ret_fwd_5 = C[t+5] / C[t] - 1
ret_fwd_20 = C[t+20] / C[t] - 1
dir_fwd_1 = 1(ret_fwd_1 > 0)
```

Forward realized volatility is computed from future one-session returns only, never from overlapping present information.

Extreme-loss labels must declare the threshold before testing.

## 10. Hypothesis lifecycle

```text
DRAFT -> REGISTERED -> RUNNING -> ACCEPTED/REJECTED/INCONCLUSIVE -> FROZEN
```

A registered hypothesis cannot be silently edited. A material rule change creates a new hypothesis ID/version.

## 11. Baseline hierarchy

Every symbolic model is compared against at least:

1. unconditional baseline;
2. Gregorian calendar baseline;
3. ordinary market-feature baseline when available;
4. randomized/null symbolic control.

## 12. Validation gates

### Gate A — data integrity
No duplicated session keys, invalid price ordering, forward-label leakage or calendar mismatch.

### Gate B — statistical sanity
Report sample count, effect size, uncertainty and multiple-testing-adjusted significance.

### Gate C — stability
Effects are inspected across market regimes and time slices.

### Gate D — walk-forward
Parameters are fitted only on past data and scored on later data.

### Gate E — null competition
True feature must outperform randomized, shifted-date or fake-origin controls.

### Gate F — sealed holdout
The final holdout is evaluated only after model/rule freeze.

## 13. Acceptance criteria

A hypothesis is not accepted because one p-value is below 0.05 or because one backtest has high return.

Minimum evidence for a candidate to graduate:

- predefined direction or explicitly exploratory status;
- adjusted statistical evidence or robust effect interval;
- stable sign in a majority of independent folds;
- positive out-of-sample incremental performance over baseline;
- meaningful advantage over registered null controls;
- no dependency on one isolated historical regime;
- reproducible run metadata and code version.

## 14. Failure conditions

Reject or downgrade a hypothesis when:

- the effect disappears after multiple-testing correction;
- shifted/randomized controls perform similarly;
- sign flips persistently across folds;
- effect exists only after post-hoc subgroup selection;
- required feature definition contains discretionary interpretation;
- results depend on leaked future data.

## 15. Rollback

Research code is version controlled. Any feature-definition change requires a new version and a changelog entry. Historical result artifacts must reference the exact Git commit and hypothesis ID.

## 16. v0.1 milestone

Deliver a deterministic baseline pipeline that:

1. reads session-level OHLCV CSV;
2. creates ordinary calendar features;
3. creates deterministic null controls;
4. builds forward-return/risk labels;
5. performs basic univariate evaluation and BH-FDR adjustment;
6. supports expanding walk-forward splits;
7. stores hypotheses in YAML.

Full astronomical Ganzhi/solar-term calculation is deliberately separated behind an engine interface and will be implemented only with a documented ephemeris/calendar convention.
