# SSE Ziping Zhenquan v1 — First Real-Market Results

Run date: 2026-08-16  
Workflow run: `31938609974`  
Commit evaluated: `f3bb0944a0e5c2b23e3d5ed57dc1c57465a010a4`  
GitHub Actions artifact ID: `9261381738`  
Artifact ZIP SHA256: `63a090edab9dd6ca4bcde93284727f91673d7d5fa60448c7e8a97d4193eafc67`

## 1. Executive result

The first preregistered SSE daily Ziping experiment does **not** provide sufficient evidence to claim that the v1 Ziping Zhenquan feature families predict Shanghai Composite next-session return or forward five-session volatility.

Decision summary:

| Hypothesis | Decision | Reason |
|---|---|---|
| ZIPING_001 | INCONCLUSIVE | No family-wide significance in development or validation; holdout contains a near-threshold wealth-polarity anomaly, but it is not stable enough for acceptance. |
| ZIPING_002 | REJECTED | Development significance does not survive later periods and shifted-session nulls are as strong or stronger. |
| ZIPING_003 | REJECTED | Formation/failure/rescue state does not survive family-wide multiple-testing correction in any partition. |
| ZIPING_004 | REJECTED | Registered volatility effects fail null competition; shifted controls are materially stronger in the sealed holdout. |

The v1 sealed holdout beginning 2021-01-01 is now **burned**. It may be inspected for diagnosis but must never again be represented as unseen evidence for a v1 rule or a rule designed after this run.

## 2. Data provenance

The first attempt using `ak.index_zh_a_hist` failed because its Eastmoney code-discovery request was disconnected upstream. The adapter was then changed to a frozen provider fallback chain and the first successful run used:

- source: AKShare / Sina index history;
- method: `ak.stock_zh_index_daily`;
- AKShare version: `1.18.84`;
- symbol: `000001`;
- first session: `1990-12-19`;
- last session: `2026-08-14`;
- observations: `8,704`;
- canonical normalized-data SHA256: `697af81a200060d42b04fa7a79b92fb8287e709ae10baf0825ae301fb4af5aa1`.

Partition sizes:

| Partition | Sessions |
|---|---:|
| development, through 2014-12-31 | 5,881 |
| validation, 2015-01-01 through 2020-12-31 | 1,462 |
| sealed_holdout_v1, 2021-01-01 onward | 1,361 |

## 3. ZIPING_001 — month-command pattern and next-session return

Family-wide minimum BH-FDR:

| Partition | Registered | Shifted null |
|---|---:|---:|
| development | 0.1323 | 0.1838 |
| validation | 0.4896 | 0.1023 |
| sealed holdout | 0.0610 | 0.8596 |

The sealed holdout produced the strongest v1 curiosity:

- `month_primary_ten_god = 偏财`: `n=138`, mean next-session return `+0.2671%`, rest `-0.0153%`, standardized effect `+0.2852`, raw `p=0.00244`, family BH-FDR `0.0610`;
- `month_primary_ten_god = 正财`: `n=132`, mean next-session return `-0.2292%`, rest `+0.0394%`, standardized effect `-0.2711`, raw `p=0.00543`, family BH-FDR `0.0678`.

This is **not accepted evidence**. Neither level passes the frozen 0.05 family-FDR gate, and the broader wealth-related behavior is not stable across earlier periods. The observation may only motivate an explicitly post-hoc, forward-only hypothesis.

## 4. ZIPING_002 — structural routes and five-session volatility

Family-wide minimum BH-FDR:

| Partition | Registered | Shifted null |
|---|---:|---:|
| development | 0.00176 | 0.00128 |
| validation | 0.27854 | 0.00449 |
| sealed holdout | 0.27900 | 0.15950 |

The development-period registered signal is not credible as a persistent Ziping effect because the shifted null is slightly stronger in the same period, and in validation the shifted null remains highly significant while the registered family does not.

**Decision: REJECTED.**

## 5. ZIPING_003 — formation/failure/rescue state and next-session return

Family-wide minimum BH-FDR:

| Partition | Registered | Shifted null |
|---|---:|---:|
| development | 0.9004 | 0.6117 |
| validation | 0.4924 | 0.4827 |
| sealed holdout | 0.2464 | 0.6594 |

No partition passes the registered family-FDR gate.

Walk-forward diagnostics do show weak sign tendencies for some state labels, for example `成候选_待强弱层` is positive in 11 of 14 eligible folds and `败候选` is negative in 11 of 14. However, those fold-level tendencies did not produce family-adjusted evidence in the preregistered partition tests and must not be promoted to a positive conclusion.

**Decision: REJECTED for v1 confirmatory use.**

## 6. ZIPING_004 — formation/failure/rescue state and five-session volatility

Family-wide minimum BH-FDR:

| Partition | Registered | Shifted null |
|---|---:|---:|
| development | 0.2024 | 0.0453 |
| validation | 0.0676 | 0.0835 |
| sealed holdout | 0.0922 | 0.00789 |

The sealed-holdout shifted-null family is substantially stronger than the registered family. A representative shifted state reaches BH-FDR `0.00789`, while the best registered holdout test is `0.0922`.

**Decision: REJECTED.**

## 7. What this experiment actually falsified

This run does not falsify every possible Bazi or Ziping-based market hypothesis. It falsifies or weakens a much narrower claim:

> A daily standalone chart, interpreted using the registered v1 month-command / structural-route / provisional formation-failure-rescue rules, provides stable daily timing information for the Shanghai Composite under the frozen v1 validation design.

That claim did not survive the complete gate.

## 8. Major limitation of v1

The v1 engine treats each trading session's 09:25 chart as a standalone Ziping chart. That is mechanically testable, but it is not the most faithful use of a natal-chart method.

A more classically coherent second branch should freeze a market natal chart first and then compute **natal chart × transit** relations. That branch must be registered as a new hypothesis family rather than used to rewrite v1 after seeing the result.

## 9. Next research gate

The next Ziping branch should therefore:

1. freeze an independently sourced SSE natal anchor;
2. compute the natal four pillars once;
3. preserve the natal month-command pattern as the base structure;
4. encode annual/monthly/daily transit ten-god and branch relations against the natal chart;
5. test whether transits strengthen, damage or rescue the frozen natal structure;
6. use a new preregistration and a new evidence boundary.

No v1 parameter is to be retuned against the burned 2021-2026 holdout.
