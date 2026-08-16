# SSE_NATAL_V1 × Transit — Historical Exploratory Results

Run date: 2026-08-16  
Workflow run: `31939164150`  
Commit evaluated: `9d8947fddfe8fd349637440371bb9b91941e4fa3`  
Artifact ID: `9261535973`  
Artifact ZIP SHA256: `cf46b2d9e634df5c5f7a01ce9b48a57996779bba380fd2766e2e9a49fc913772`

## 1. Evidence status

**Exploratory only.** No observation through 2026-08-14 is treated as a new holdout.

The frozen natal anchor is `1990-12-19 11:00 Asia/Shanghai`. Under the frozen `lunar_python==1.4.8` convention, the engine produces:

```text
庚午年 戊子月 戊午日 戊午时
日主：戊
月令候选：财格
月令本气十神：正财
用法：顺用
```

These pillars are an operational calculation under the registered convention, not an assertion of metaphysical causality.

## 2. Data provenance

- source: AKShare / Eastmoney direct index history;
- method: `ak.stock_zh_index_daily_em`;
- AKShare version: `1.18.84`;
- symbol: `000001`;
- first date: `1990-12-19`;
- last date: `2026-08-14`;
- rows: `8,704`;
- canonical SHA256: `ca752500245963330ca3fbe5938cf1a29f12fc6d1e4e984149d325081efabb59`.

The prior standalone-Ziping run happened to use the Sina fallback and therefore has a different canonical dataset hash. Provider reconciliation is required before cross-branch numerical comparisons are treated as exact.

## 3. Controls

The real natal chart was compared against two pre-registered null classes:

### Shifted-session nulls

The real relation features were displaced by:

- 17 trading sessions;
- 31 trading sessions;
- 47 trading sessions.

### Fake natal anchors

The same relation engine was recomputed from three arbitrary control anchors:

- `SSE_FAKE_NATAL_P17`: 1991-01-05 11:00;
- `SSE_FAKE_NATAL_P31`: 1991-01-19 11:00;
- `SSE_FAKE_NATAL_P47`: 1991-02-04 11:00.

The fake-anchor family contains three times as many anchor variants and therefore receives a larger multiple-testing penalty than the one real natal anchor.

## 4. SSE_NATAL_001 — daily transit relations → next-session return

Family-wide minimum BH-FDR values:

| Era | Real natal | Fake natal | Shift null |
|---|---:|---:|---:|
| 1990-2004 | 0.3180 | 0.2405 | 0.9017 |
| 2005-2014 | 0.6161 | 0.5719 | 0.7516 |
| 2015-2020 | 0.3569 | 0.3399 | 0.3707 |
| 2021-2026 | 0.4875 | 0.6770 | 0.5408 |
| full history | 0.1798 | 0.1321 | 0.9635 |

No real-natal return family passes the 0.05 family-FDR gate in any descriptive era or in the full historical sample.

**Exploratory decision: NO RETURN CANDIDATE.**

There is no basis in this run to claim that the frozen SSE natal chart and daily transits predict next-session Shanghai Composite return.

## 5. SSE_NATAL_002 — transit structural relations → forward five-session volatility

Family-wide minimum BH-FDR values:

| Era | Real natal | Fake natal | Shift null |
|---|---:|---:|---:|
| 1990-2004 | 1.11e-11 | 3.98e-18 | 2.06e-15 |
| 2005-2014 | 1.35e-14 | 2.38e-28 | 1.72e-21 |
| 2015-2020 | 1.44e-25 | 5.98e-30 | 4.36e-28 |
| 2021-2026 | 1.31e-10 | 1.90e-10 | 6.26e-08 |
| full history | 1.17e-09 | 4.40e-16 | 5.34e-07 |

There is a strong historical association between the registered cyclical relation primitives and forward five-session volatility. However, **the association is not specific to the real natal anchor**:

- fake natal controls are stronger than the real natal family in 1990-2004, 2005-2014, 2015-2020 and the full-history view;
- shifted-session controls also remain strongly significant;
- the leading feature changes materially across eras;
- in 2021-2026, one fake-anchor month-clash state selects the exact same 101 observations and the same effect size as the leading real-natal state, despite a different arbitrary natal date.

A representative full-history real-natal result is:

```text
feature: natal_transit__v1__branch_break_count
level: 3
n: 1,563
future-5-session volatility mean: 1.2527%
rest mean: 1.4736%
standardized effect: -0.1297
family BH-FDR: 1.17e-09
```

But the strongest fake-natal full-history result reaches BH-FDR `4.40e-16`, despite the fake family paying a larger multiplicity penalty.

**Exploratory decision: ASSOCIATION PRESENT, NATAL-ANCHOR SPECIFICITY REJECTED.**

The defensible interpretation is that these features are acting as deterministic calendar/cycle encodings associated with volatility regimes. This run does not support attributing that information to the specific SSE natal anchor.

## 6. What this run falsifies

The following stronger claim is not supported:

> The exact 1990-12-19 11:00 SSE natal chart has unique predictive information for daily returns or five-session volatility that arbitrary nearby natal anchors and displaced features do not have.

The return part shows no robust historical candidate. The volatility part fails the natal-specificity test.

## 7. What remains interesting

The volatility result is not useless. It points to a different research question:

> Do deterministic Chinese calendar states — independent of any natal-chart story — contain stable information about A-share volatility regimes?

That question belongs in the Ganzhi / solar-term / calendar branch and should be tested directly against Gregorian calendar and randomized controls rather than wrapped in a natal-chart explanation.

## 8. Data-source warning

The successful first standalone-Ziping run used the Sina AKShare provider, while this run used the direct Eastmoney provider. Both returned 8,704 dates but their canonical hashes differ. Most close-price differences are tiny, but a small number of early historical sessions differ materially.

Before branch-to-branch effect sizes are ranked, MetaAlpha should add provider pinning and a cross-provider reconciliation report. Statistical conclusions that survive both datasets deserve more confidence than conclusions tied to one upstream vendor.

## 9. Next gate

Recommended next work:

1. freeze a canonical market-data provider or consensus/reconciliation rule;
2. rerun registered Ganzhi and solar-term volatility families directly;
3. compare them against Gregorian month/weekday/seasonality baselines and the same shifted/random controls;
4. stop spending development effort on the SSE natal-anchor branch unless future forward evidence gives a reason to reopen it.
