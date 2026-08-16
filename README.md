# MetaAlpha

**MetaAlpha** is a falsifiable research framework for testing whether traditional Chinese temporal-symbolic systems contain statistically useful information for A-share market forecasting.

The project does **not** assume that Ganzhi, Wuxing, Bazi, Qimen, Yijing, Meihua or Liuyao are predictive. It treats each rule family as a registered hypothesis generator and subjects it to the same statistical and out-of-sample tests as ordinary calendar factors, market factors and randomized controls.

## Core principle

> Freeze the rule first. Test second. Never rewrite the rule after seeing the result.

A candidate survives only if it remains useful after:

- multiple-testing correction;
- walk-forward validation;
- regime stability checks;
- randomized/null controls;
- transaction-cost assumptions where applicable;
- sealed holdout evaluation.

## Current scope — v0.2

The first Bazi implementation is explicitly based on a **Ziping Zhenquan (《子平真诠》) month-command-first operationalization**.

Implemented branches:

1. Gregorian calendar controls;
2. solar-term-aware Ganzhi pillars;
3. stem/branch element and polarity mappings;
4. Ziping ten-god mapping;
5. month-command hidden stems and transmitted-stem features;
6. Ziping pattern candidates: 官、财、印、食神、七杀、伤官、阳刃、建禄月劫;
7. 顺用/逆用 structural route flags;
8. month-command 冲、害、破、刑 flags;
9. deterministic randomized controls;
10. forward return/risk labels and statistical screening.

Qimen, Meihua, Yijing and true-random Liuyao remain later branches. True-random Liuyao is **forward-test only**.

## Why Ziping is not a five-element score

MetaAlpha v0.2 deliberately does not start by assigning arbitrary weights to “木火土金水强弱”. The Ziping branch first records:

```text
月令 -> 十神 -> 格局候选 -> 顺/逆 -> 四柱配合 -> 成败/制化 primitive flags
```

Strength and pattern-quality models such as 有情/无情、有力/无力 are deferred until their numerical rules can be independently versioned and tested. This prevents a large discretionary weight surface from becoming a backtest-overfitting machine.

## Research questions

### H1 — marginal information

Does a traditional temporal feature change the conditional distribution of future return/risk?

### H2 — relational information

Do relationship rules such as month-command structure, stem transmission and branch interactions add information beyond raw calendar labels?

### H3 — incremental alpha

Does the symbolic feature family improve out-of-sample performance after ordinary calendar and market variables are already included?

## Targets

Initial targets include:

- next-session return;
- forward 5-session return;
- forward 20-session return;
- next-session direction;
- forward volatility;
- extreme-loss probability.

## Validation hierarchy

1. Univariate sanity checks
2. Multiple-testing correction
3. Regime stability
4. Walk-forward validation
5. Randomized/date-shift controls
6. Sealed holdout

Historical backtest beauty is not an acceptance criterion.

## Repository layout

```text
MetaAlpha/
├── docs/
│   ├── RFC-0001-metaalpha-v0.1.md
│   ├── RFC-0002-ziping-zhenquan-bazi.md
│   ├── HYPOTHESIS_REGISTRY.md
│   └── VALIDATION_STANDARD.md
├── registry/
│   └── hypotheses.yaml
├── src/metaalpha/
│   ├── bazi_ziping.py
│   ├── calendar_features.py
│   ├── controls.py
│   ├── ganzhi.py
│   ├── labels.py
│   ├── pipeline.py
│   └── validation.py
├── tests/
│   ├── test_controls.py
│   ├── test_ganzhi_ziping.py
│   └── test_labels.py
├── pyproject.toml
└── README.md
```

## Calendar convention

The v0.2 A-share session convention is frozen as:

```text
timezone: Asia/Shanghai
session feature anchor: 09:25:00
calendar engine: lunar_python 1.4.8
```

Alternative anchors or calendrical conventions must be registered as new hypotheses rather than silently optimized.

## Running the pipeline

Baseline only:

```bash
metaalpha input.csv --out reports/baseline
```

Enable Ganzhi + Ziping Zhenquan features:

```bash
metaalpha input.csv --ziping --out reports/ziping_v1
```

Expected minimum input:

```text
date,close
2024-01-02,2962.28
...
```

For cross-sectional work, add `symbol` and preferably full OHLCV/amount/turnover data.

## Non-goals

- no claim of supernatural causality;
- no live trading recommendation engine at this stage;
- no discretionary post-hoc interpretation;
- no LLM-generated daily metaphysical narrative as a feature source;
- no model selection based only on highest historical return;
- no hidden rule changes after seeing market results.

## Status

`v0.2.0-alpha` — deterministic Ganzhi + Ziping Zhenquan primitive feature engine, registered hypotheses, tests and CI.
