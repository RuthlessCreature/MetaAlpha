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

## v0.1 scope

Phase 1 deliberately starts with the most deterministic and historically reconstructable branches:

1. Gregorian calendar controls;
2. Ganzhi features;
3. Wuxing mappings;
4. 24 solar terms;
5. Bazi-compatible feature interfaces;
6. randomized and date-shift controls.

Qimen, Meihua, Yijing and true-random Liuyao are later branches. True-random Liuyao is **forward-test only**.

## Research questions

### H1 — marginal information

Does a traditional temporal feature change the conditional distribution of future return/risk?

### H2 — relational information

Do relationship rules such as stem/branch interactions add information beyond raw calendar labels?

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
│   ├── HYPOTHESIS_REGISTRY.md
│   └── VALIDATION_STANDARD.md
├── registry/
│   └── hypotheses.yaml
├── src/metaalpha/
│   ├── __init__.py
│   ├── calendar_features.py
│   ├── controls.py
│   ├── labels.py
│   ├── pipeline.py
│   └── validation.py
├── tests/
│   ├── test_controls.py
│   └── test_labels.py
├── pyproject.toml
└── README.md
```

## Non-goals of v0.1

- no claim of supernatural causality;
- no live trading recommendation engine;
- no discretionary post-hoc interpretation;
- no LLM-generated daily metaphysical narrative as a feature source;
- no model selection based only on highest historical return.

## Status

`v0.1.0-alpha` — research specification and deterministic baseline pipeline.
