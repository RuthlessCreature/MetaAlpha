# Validation Standard

## 1. Principle

MetaAlpha optimizes for falsification resistance, not attractive backtests.

## 2. Metrics

Depending on target/model, report at least:

- sample count;
- mean/median forward return;
- effect size versus baseline;
- t statistic where appropriate;
- confidence interval;
- hit rate;
- AUC for binary direction models;
- IC / rank IC for cross-sectional models;
- Sharpe only when a tradable portfolio rule is explicitly defined;
- maximum drawdown and turnover for portfolio tests.

## 3. Multiple testing

Raw p-values are never the final decision criterion when several related hypotheses are tested. v0.1 implements Benjamini-Hochberg FDR adjustment. Later versions may add White Reality Check, SPA, PBO and Deflated Sharpe Ratio.

## 4. Walk-forward

Use expanding or rolling splits where all training timestamps precede validation timestamps. No random K-fold split is allowed for market forecasting.

## 5. Stability

A candidate should be sliced by at least:

- chronological fold;
- bull/bear/sideways regime when a preregistered regime definition exists;
- high/low volatility regime;
- large/small-cap bucket for cross-sectional studies.

Regime definitions must be created without looking at the candidate factor's performance.

## 6. Null controls

At least one null/control should be registered for each feature family. Preferred controls:

- deterministic random labels derived from cryptographic hashing;
- date-shifted symbolic features;
- fake stock/index origin dates;
- Gregorian calendar features.

## 7. Sealed holdout

The holdout period must be declared before final evaluation and must not be used for feature engineering, threshold setting or school/convention selection.

## 8. Graduation rule

A feature family may advance to trading simulation only when it shows incremental out-of-sample value over baseline and materially beats its null controls. A visually impressive in-sample equity curve is insufficient.
