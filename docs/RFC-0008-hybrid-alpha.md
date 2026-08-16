# RFC-0008 — HYBRID_ALPHA_001

## Purpose

Test whether deterministic Chinese symbolic-time states add **incremental out-of-sample predictive information** beyond a conventional lagged-market baseline.

This RFC does not test metaphysical causality. It tests whether the frozen symbolic state vector improves probabilistic market forecasts after ordinary lagged return, volatility, range, trend and volume information is already available to the model.

## Prediction clock

The prediction is formed at **09:25 Asia/Shanghai** on trading session `t`.

The target is the same session close-to-close direction:

`ret_session_t = close_t / close_{t-1} - 1`

`direction_t = 1(ret_session_t > 0)`

All market predictors must be observable no later than the close of `t-1`. Symbolic predictors are deterministic states computed for 09:25 on `t`.

## Why this experiment exists

Previous MetaAlpha branches show a repeated pattern:

- direct symbolic variables can exhibit historically strong local associations;
- many associations fail full-history stability, shifted-state controls, non-overlap robustness, or forward-promotion gates;
- therefore the next defensible question is not whether a symbolic system independently predicts the market, but whether it contributes a small conditional improvement to an ordinary market model.

## Frozen market baseline

The baseline contains only lagged market information:

- 1/2/5/10/20-session lagged returns;
- previous-session absolute return;
- 5/20-session lagged realized volatility;
- previous-session overnight gap;
- previous-session intraday high-low range;
- close distance from lagged 5/20-session moving averages;
- 20-session trailing drawdown;
- lagged log volume change and 20-session volume z-score when volume exists;
- secular normalized time and its square;
- Gregorian weekday and month fixed effects.

No same-session open, high, low, close, volume or return is permitted as a predictor.

## Frozen symbolic blocks

### Cycle

Raw deterministic Chinese-calendar states from `calendar_cycle_v1`:

- previous solar term;
- solar-term phase quartile;
- day pillar;
- month stem;
- month branch.

### Qimen

Raw `QIMEN_V1` plate states at 09:25:

- dun / ju / yuan state;
- duty star-door pair;
- duty landings;
- rotation state;
- void relation state;
- yima relation state.

### Ziping

Frozen structural outputs already implemented before this experiment:

- v2 selected ten-god;
- v2 selection reason;
- v3 route state;
- v4 wealth-resource position resolution;
- v4 selected-use root bin;
- v4 support profile.

### All-symbolic

The union of the three frozen blocks. No post-hoc deletion of individual symbolic features is permitted after results are observed.

## Model

Primary model: ridge logistic regression.

- one-hot encoding for categorical variables;
- standard scaling for continuous variables;
- `C ∈ {0.01, 0.1, 1, 10}`;
- hyperparameter chosen inside each outer training sample using an expanding inner time split and log loss;
- no random shuffle cross-validation.

A deliberately simple linear probabilistic model is used first. A nonlinear model is not allowed to rescue a failed v1 experiment.

## Outer walk-forward

Expanding training windows, with frozen OOS tests:

1. 2010–2013
2. 2014–2017
3. 2018–2021
4. 2022–2026-08-14

Rows at train/test boundaries are separated by a one-session embargo.

## Metrics

Primary:

- LogLoss
- Brier score

Secondary:

- ROC AUC
- accuracy
- calibration slope
- return spread between high- and low-probability buckets

Every symbolic model is compared with the baseline on the **same OOS rows**.

## Promotion gate

A symbolic block is historically interesting only if all frozen conditions hold:

- LogLoss improves in at least 3 of 4 outer windows;
- Brier improves in at least 3 of 4 outer windows;
- full-OOS LogLoss improvement is at least 0.001;
- full-OOS Brier improvement is at least 0.0005;
- ROC AUC is not worse by more than 0.005;
- a 20-session block bootstrap with 2,000 repetitions assigns at least 95% one-sided probability that the augmented model improves the primary loss.

Passing this gate still does **not** create confirmatory evidence. It only qualifies the frozen model for a separately registered future-only test.

## Failure interpretation

If a block fails, the conclusion is limited to the frozen representation/model. The failed result must not be used to tune feature subsets or conventions and rerun under the same hypothesis ID.
