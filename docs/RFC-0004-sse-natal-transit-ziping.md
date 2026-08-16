# RFC-0004: SSE Natal Chart × Transit Ziping Branch

Status: **REGISTERED FOR EXPLORATORY HISTORICAL RESEARCH; CONFIRMATION FORWARD-ONLY**  
Date frozen: 2026-08-16

## 1. Why this branch exists

The first Ziping v1 experiment classified each trading session as a standalone chart. That is deterministic and falsifiable, but it is not the most natural interpretation of a natal-chart method.

This RFC creates a separate branch in which one independently sourced Shanghai market natal event is frozen once and subsequent market sessions are represented as transits against that natal chart.

This is a **new hypothesis family**. It does not rewrite or rescue the failed/inconclusive v1 hypotheses.

## 2. Frozen natal anchor

`SSE_NATAL_V1` is fixed to:

```text
1990-12-19 11:00:00 Asia/Shanghai
```

Rationale:

- Shanghai Stock Exchange states that it formally opened on 1990-12-19.
- China Securities Museum, operated within the SSE system, records that at **11:00 on 1990-12-19** the first-generation opening gong was struck in the first trading hall and marked the formal opening of the centralized capital market.

Primary references:

- https://www.sse.com.cn/aboutus/sseintroduction/introduction/
- https://csm.sse.com.cn/news/list/c/c_20260108_10804601.shtml

The exact 11:00 event is preferred over inventing a 09:30 birth time.

## 3. Calendrical convention

- timezone: Asia/Shanghai;
- natal anchor: 1990-12-19 11:00;
- transit session anchor: 09:25 on each trading session;
- engine: `lunar_python==1.4.8`;
- natal chart is calculated once and never changed inside v1 of this branch.

## 4. Static natal layer

The engine records:

- natal year/month/day/time pillars;
- natal day master;
- natal month-command pattern candidate;
- natal month primary ten-god;
- natal 顺用/逆用 classification.

Static natal features are metadata and are not themselves predictive variables within one-index time-series tests because they do not vary by session.

## 5. Transit relation primitives

For transit year, month, day and market-anchor time, the engine records:

- transit stem ten-god relative to natal day master;
- transit branch primary-hidden-stem ten-god relative to natal day master;
- heavenly-stem combination count with natal stems;
- earthly-branch clash count with natal branches;
- harm count with natal branches;
- break count with natal branches;
- 六合 count with natal branches.

It additionally records specific transit-day relations against the natal day and natal month branches.

## 6. No hand-tuned fortune score

The engine explicitly emits:

```text
natal_transit__v1__fortune_score_defined = 0
```

No positive/negative weights are assigned to combinations, clashes, harms, wealth, official, resource or output features in this RFC.

If a later model combines primitives into a score, that score is a separate registered hypothesis and must declare all weights before evaluation.

## 7. Evidence boundary

All market outcomes through 2026-08-14 have already been used in MetaAlpha development and/or v1 diagnosis.

Therefore:

- historical natal-transit results through 2026-08-14 are **exploratory only**;
- no historical interval through that date may be called a new sealed holdout for this branch;
- confirmatory evidence starts with trading sessions after the freeze date;
- the intended first forward session boundary is 2026-08-17 or the next actual SSE trading session if the market is closed.

## 8. Initial targets

Exploratory targets remain:

- `ret_fwd_1`;
- `ret_fwd_5`;
- `vol_fwd_5`;
- `extreme_loss_fwd_1`.

## 9. Null controls

Natal-transit features must compete against:

- shifted-session versions at fixed lags;
- Gregorian calendar variables;
- ordinary market-state variables when introduced;
- fake natal anchors in later experiments, registered before comparison.

A natal relation that performs no better than a shifted or fake-anchor relation is not evidence for the natal-anchor hypothesis.

## 10. Acceptance rule

No historical exploratory result can confirm this branch.

A feature family may graduate only after a separately defined forward protocol reaches its prespecified sample threshold and survives:

1. family-wide multiple-testing correction;
2. null competition;
3. effect-direction stability;
4. economically meaningful effect size;
5. reproducible data provenance.

## 11. Future extension

After primitive testing, a later RFC may encode pattern-specific transit effects such as whether a transit introduces a registered failure or rescue condition into the frozen natal structure. That state machine must be versioned separately and may not be inferred after observing its target period.
