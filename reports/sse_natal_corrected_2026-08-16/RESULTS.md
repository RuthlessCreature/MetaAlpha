# SSE_NATAL_V1 × Transit — Corrected Historical Exploration

Run date: 2026-08-16  
Workflow run: `31939815944`  
Commit evaluated: `7371dd40fe2028a4ef374c016acc23a14f6b2e8d`  
Artifact ID: `9261714991`  
Artifact ZIP SHA256: `fdab1036e3de6b97a2f5f29131e14fbf73a2c9fba78a5da92959821eb35d6c50`

## 1. Status

This corrected run supersedes the inferential interpretation of the earlier SSE natal-transit historical exploration.

All observations through 2026-08-14 are **exploratory only**. The natal branch was defined after historical outcomes had already been exposed, so none of these periods is a confirmatory holdout.

Corrections applied:

- canonical Sina market data;
- strictly future-only volatility labels;
- target-horizon purging at era boundaries;
- OLS Newey-West/HAC inference;
- family-wide BH-FDR;
- real natal anchor compared against shifted-session and fake-natal controls.

## 2. Data and frozen natal chart

Market data:

- source: Sina via `ak.stock_zh_index_daily`;
- AKShare version: `1.18.84`;
- rows: `8,704`;
- first date: `1990-12-19`;
- last date: `2026-08-14`;
- canonical SHA256: `697af81a200060d42b04fa7a79b92fb8287e709ae10baf0825ae301fb4af5aa1`.

Frozen natal anchor:

```text
SSE_NATAL_V1
1990-12-19 11:00 Asia/Shanghai
庚午年 戊子月 戊午日 戊午时
日主：戊
月令候选：财格
月令本气十神：正财
用法：顺用
```

Control natal anchors remain fixed at +17, +31 and +47 calendar days from the real anchor. Shift controls remain fixed at 17, 31 and 47 trading sessions.

## 3. SSE_NATAL_001 — natal/transit relations and next-session return

Family-wide minimum BH-FDR:

| Historical era | Real natal | Fake natal | Shift null |
|---|---:|---:|---:|
| 1990-2004 | 0.4636 | 0.3506 | 0.8944 |
| 2005-2014 | 0.1356 | 0.6313 | 0.7433 |
| 2015-2020 | 0.4741 | 0.4625 | 0.3126 |
| 2021-2026 | 0.5885 | 0.6700 | 0.4513 |
| full history | 0.1423 | 0.1917 | 0.9610 |

No real-natal return family passes the 0.05 family-FDR gate in any era or in the full sample.

**Decision: no historical return candidate.**

## 4. SSE_NATAL_002 — natal/transit structural relations and forward five-session volatility

Family-wide minimum BH-FDR:

| Historical era | Real natal | Fake natal | Shift null |
|---|---:|---:|---:|
| 1990-2004 | 0.1126 | **0.0000162** | **0.00306** |
| 2005-2014 | **0.02694** | **0.000735** | **0.0000946** |
| 2015-2020 | **0.00283** | **0.00920** | **0.000627** |
| 2021-2026 | 0.1279 | 0.1802 | **0.03852** |
| full history | **0.0000845** | **0.000917** | **0.04460** |

The full-history real-natal family contains a strong statistical association. Its leading level is:

```text
feature: natal_transit__v1__branch_break_count
level: 6
n: 156
mean forward-5-session volatility: 1.0214%
rest mean: 1.4404%
standardized effect: -0.2463
HAC t-stat: -4.7914
raw p-value: approximately 1.66e-6
family BH-FDR: 8.45e-5
HAC maxlags: 20
```

However, the pattern fails the **natal-anchor specificity** requirement:

- 1990-2004: the real natal family is non-significant while both fake natal and shifted controls are significant;
- 2005-2014: the real natal family passes 0.05, but fake natal and shifted controls are substantially stronger;
- 2015-2020: the real natal family is significant, but shifted controls are stronger;
- 2021-2026: the real natal family is non-significant while a shifted control still passes 0.05;
- full history: real, fake and shifted families all contain significant associations.

The strongest registered feature also changes across historical eras rather than forming a stable natal-specific rule.

**Decision: historical cycle association present; SSE natal-anchor specificity rejected.**

## 5. Interpretation

The corrected evidence supports a narrower research interpretation:

> Deterministic cyclical/calendar relation variables can partition historical Shanghai Composite five-session volatility distributions.

It does **not** support the stronger interpretation:

> The exact 1990-12-19 11:00 SSE natal chart has unique predictive information that nearby arbitrary natal anchors or displaced versions of the same features do not possess.

The control families are essential here. Without fake anchors and displaced features, the full-history `8.45e-5` FDR could easily be misrepresented as evidence for the natal-chart story.

## 6. Research decision

- Do not tune or deepen `SSE_NATAL_V1` merely to rescue natal-anchor specificity.
- Keep the branch available for future forward evidence, but deprioritize it.
- Move the volatility question into a direct Ganzhi / solar-term / calendar-cycle branch where the hypothesis is tested without a natal-chart narrative.
- Any future natal-specific claim must beat fake anchors and shifted controls under the same corrected inference protocol.
