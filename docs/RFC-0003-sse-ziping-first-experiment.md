# RFC-0003: First SSE Ziping Zhenquan Experiment

Status: **FROZEN FOR FIRST RUN**  
Date: 2026-08-16  
Scope: Shanghai Composite Index (`000001`) daily sessions

## 1. Purpose

Run the first real-market MetaAlpha experiment using the already registered Ziping Zhenquan feature engines. The objective is not to prove metaphysical causality. The objective is to determine whether the frozen symbolic state variables contain reproducible statistical information beyond obvious nulls.

## 2. Market data

Primary adapter:

- library: `akshare==1.18.84`
- public function: `ak.index_zh_a_hist`
- index code: `000001`
- period: daily
- requested start: `19901219`
- upstream: Eastmoney as exposed by AKShare

Reference documentation:

- https://akshare.akfamily.xyz/data/index/index.html
- https://pypi.org/project/akshare/

The upstream endpoint is external and has had availability incidents. Therefore every run MUST store:

- AKShare version;
- fetch UTC timestamp;
- requested interval;
- returned row count;
- first/last session date;
- canonical SHA256 of normalized OHLCV data.

An empty result, changed required schema, invalid OHLC ordering or non-positive OHLC values fails the run.

## 3. Time convention

All symbolic features use the convention frozen in RFC-0002:

- timezone: Asia/Shanghai;
- session anchor: 09:25 local civil time;
- calendrical engine: `lunar_python==1.4.8`;
- month/year transition: solar-term-aware convention supplied by the frozen engine.

## 4. Registered hypotheses in this run

### ZIPING_001 — month-command pattern → next-session return

Target: `ret_fwd_1`

Features:

- `zpzt__v1__month_primary_ten_god`
- `zpzt__v1__pattern_candidate`
- `zpzt__v1__use_mode`
- `zpzt__v1__month_hidden_transmitted_count`
- `zpzt__v1__month_disruption_count`

### ZIPING_002 — structural routes → forward 5-session volatility

Target: `vol_fwd_5`

Features:

- `zpzt__v1__route_hit_count`
- `zpzt__v1__month_clash`
- `zpzt__v1__month_harm`
- `zpzt__v1__month_break`
- `zpzt__v1__month_punishment`

### ZIPING_003 — provisional 成/败/救应 state → next-session return

Target: `ret_fwd_1`

Features:

- `zpzt_state__v1__state`
- `zpzt_state__v1__formation_hit`
- `zpzt_state__v1__failure_hit`
- `zpzt_state__v1__rescue_hit`
- `zpzt_state__v1__requires_strength`

### ZIPING_004 — provisional 成/败/救应 state → forward 5-session volatility

Target: `vol_fwd_5`

Features are identical to ZIPING_003.

## 5. Partitions frozen before first run

The first run uses three chronological partitions:

| Partition | Interval | Role |
|---|---|---|
| development | first available session — 2014-12-31 | early evidence only |
| validation | 2015-01-01 — 2020-12-31 | later independent period |
| sealed_holdout_v1 | 2021-01-01 — latest returned session | one-time final v1 check |

The `sealed_holdout_v1` interval is **burned after the first successful evaluation**. Any rule or weight changed after viewing it must create a new version and may not claim this same interval as unseen evidence.

## 6. Statistical tests

For each registered family and partition:

1. one-vs-rest Welch t-test for each eligible categorical level;
2. standardized conditional-mean effect size;
3. Benjamini-Hochberg correction across **all tested levels in the whole registered feature family**, not separately per feature;
4. minimum 100 observations per tested level and comparison group in the production run.

A low unadjusted p-value is never sufficient evidence.

## 7. Null competition

Each registered feature is copied into deterministic shifted-session controls using:

- 17 trading sessions;
- 31 trading sessions;
- 47 trading sessions.

The shifted feature is evaluated with the same target, minimum sample threshold and family-wide FDR procedure.

The purpose is to detect cases where a result is merely a broad calendar/regime artifact that survives arbitrary displacement.

## 8. Walk-forward stability

Frozen features are additionally measured on successive future-only blocks:

- first 1500 rows excluded as initial history;
- test block: 500 sessions;
- no test block is used to construct an earlier block;
- the walk-forward table is diagnostic and is not used to retune v1 rules.

## 9. Output contract

A successful run produces:

```text
reports/sse_ziping_first/
├── dataset.csv
├── data_manifest.json
├── run_metadata.json
├── registered_and_null_screens.csv
├── walk_forward_stability.csv
├── diagnostic_summary.csv
└── SUMMARY.md
```

## 10. Interpretation gate

No hypothesis is accepted merely because it is significant in development data.

A candidate deserves further study only if later-period evidence is not materially weaker than the shifted null competition and the effect does not depend on one isolated historical regime. The first run is a discovery/triage event; it is not a trading authorization.

## 11. Failure conditions

The run fails or the hypothesis is downgraded if any of the following occurs:

- upstream data cannot be reproduced or validated;
- family-wide FDR removes the apparent effect;
- shifted controls are comparable or stronger;
- direction/effect collapses in validation or the sealed holdout;
- results require post-hoc changes to the classical rule definition;
- the result depends on leaked future information.

## 12. Next research gate

Only after this experiment should MetaAlpha decide whether to:

1. deepen Ziping state modelling;
2. move to cross-sectional stock-level birth-chart/transit experiments;
3. add Qimen/Meihua/Yijing branches;
4. reject or pause Ziping if it fails null/OOS competition.
