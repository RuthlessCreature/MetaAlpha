# MetaAlpha

**MetaAlpha** is a falsifiable research framework for testing whether traditional Chinese temporal-symbolic systems contain statistically useful information for A-share market forecasting.

The project does **not** assume that Ganzhi, Wuxing, Bazi, Qimen, Yijing, Meihua or Liuyao are predictive. Every rule family is treated as a versioned hypothesis generator and must compete against ordinary calendar factors, displaced/randomized controls and genuinely future observations.

## Core rule

> Freeze the rule first. Commit the signal before the outcome exists. Test once at the registered gate. Never rewrite the rule after seeing the result.

Historical backtest beauty is not acceptance.

## Current status — v0.4.0-alpha

The implemented Bazi branch is based on a **Ziping Zhenquan (《子平真诠》) month-command-first operationalization**:

```text
月令 -> 十神 -> 格局候选 -> 顺/逆 -> 四柱配合 -> 成败/制化 primitive flags
```

Implemented research components include:

1. Gregorian calendar controls;
2. solar-term-aware Ganzhi pillars;
3. deterministic ten-god mapping;
4. month-command hidden stems and transmission;
5. pattern candidates: 官、财、印、食神、七杀、伤官、阳刃、建禄月劫;
6. 顺用/逆用 route flags;
7. month-command 冲、害、破、刑 primitives;
8. provisional 成/败/救应 state machine;
9. frozen SSE natal-anchor × transit branch with fake-anchor controls;
10. multi-provider market-data reconciliation;
11. corrected future-only return/volatility labels;
12. HAC/Newey-West time-series inference;
13. immutable forward-only precommit/scoring workflow.

Qimen, Meihua, Yijing and true-random Liuyao remain later branches. True-random Liuyao is forward-test only.

## What the first historical experiments actually found

The first research pass exposed two methodology failures that are now explicitly recorded rather than hidden:

- the prototype `vol_fwd_5` implementation did **not** strictly use `t+1..t+5` returns;
- ordinary IID Welch tests understated time-series dependence for overlapping forward targets.

Those volatility results are invalidated. The corrected pipeline uses strictly future-only labels, target-horizon boundary purging and HAC/Newey-West covariance.

Under the corrected standalone Ziping analysis:

- `ZIPING_002` and `ZIPING_004` do not retain the earlier apparent volatility evidence;
- `ZIPING_003` remains unsupported for next-session return;
- the only surviving historical curiosity is the already-exposed 2021+ level `zpzt__v1__month_primary_ten_god = 偏财` for next-session return.

Because that 2021+ interval was already inspected, the 偏财 result is **not confirmation**. It only nominates `ZIPING_FWD_001`, whose evidence starts on 2026-08-17.

The corrected `SSE_NATAL_V1` branch also does not support a unique natal-anchor explanation: next-session return evidence is absent, while historical volatility associations can be matched or exceeded by fake natal anchors and shifted-session controls.

## ZIPING_FWD_001 — true forward test

Frozen rule:

```text
feature: zpzt__v1__month_primary_ten_god
level: 偏财
target: ret_fwd_1
forecast on 偏财: positive next-session return
forecast otherwise: no_call
feature anchor: 09:25 Asia/Shanghai
forward evidence start: 2026-08-17
market data provider: Sina via ak.stock_zh_index_daily
```

Every weekday candidate is precommitted before the result exists. An existing signal file cannot be overwritten. A record generated after 09:25 on its signal date is automatically ineligible for confirmation. Holidays may be precommitted, but are scored only if the pinned market data confirms that date was an actual trading session.

The first immutable record is:

```text
2026-08-17
pillars: 丙午 丙申 癸亥 丁巳
month_primary_ten_god: 正印
signal: 0
forecast: no_call
```

That no-call is retained. The experiment does not cherry-pick only 偏财 days into the audit trail.

### One-time acceptance gate

The first time all sample thresholds are met, the gate is evaluated once and written to an immutable `gate_result.json`.

Requirements:

- at least 300 scored market sessions;
- at least 30 偏财 signal sessions;
- calendar-adjusted signal coefficient ≥ +10 bp;
- one-sided `p <= 0.025`;
- positive raw signal-minus-rest difference in both chronological halves;
- signal beta must exceed the 17/31/47 actual-session shifted controls.

Primary model:

```text
ret_fwd_1 ~ I(month_primary_ten_god == 偏财) + weekday fixed effects + Gregorian month fixed effects
covariance: Newey-West HAC, maxlags=5
```

Once the gate is written, later daily monitoring cannot reverse the first decision.

## Data provenance

Confirmatory comparisons do not use automatic provider switching.

The current canonical forward provider is **Sina**. The corrected provider reconciliation found:

- Sina: 8,704 sessions, 1990-12-19 through 2026-08-14;
- Tencent: 8,694 sessions over the comparable range, omitting 10 Sina dates;
- among common dates, no corrected daily-return disagreement exceeded 100 bp;
- Eastmoney direct was unavailable during the reconciliation run.

Provider choice is based on completeness/reproducibility, not which source improves a research result.

## Repository layout

```text
MetaAlpha/
├── .github/workflows/
│   ├── ci.yml
│   ├── data-reconciliation.yml
│   ├── forward-ziping.yml
│   ├── research-sse.yml
│   └── research-sse-natal.yml
├── docs/
├── forward/
│   └── ZIPING_FWD_001/
│       ├── signals/
│       └── status/                 # created as future outcomes arrive
├── registry/
│   ├── hypotheses.yaml
│   ├── natal_hypotheses.yaml
│   └── forward_hypotheses.yaml
├── reports/
├── src/metaalpha/
│   ├── bazi_ziping.py
│   ├── data_reconcile.py
│   ├── data_sources.py
│   ├── forward_ziping.py
│   ├── ganzhi.py
│   ├── labels.py
│   ├── natal_transit.py
│   ├── research_natal.py
│   ├── research_ziping.py
│   └── validation.py
└── tests/
```

## Calendar convention

Frozen A-share feature convention:

```text
timezone: Asia/Shanghai
session feature anchor: 09:25:00
calendar engine: lunar_python 1.4.8
```

Alternative anchors or calendrical conventions require a new hypothesis/version.

## Running

Install:

```bash
pip install -e '.[dev,data]'
```

Baseline pipeline:

```bash
metaalpha input.csv --out reports/baseline
```

Standalone Ganzhi + Ziping features:

```bash
metaalpha input.csv --ziping --out reports/ziping_v1
```

Generate one forward precommit manually:

```bash
metaalpha-ziping-forward signal \
  --date 2026-08-17 \
  --out forward/ZIPING_FWD_001/signals/2026-08-17.json
```

Score currently realized evidence using the pinned provider:

```bash
metaalpha-ziping-forward score \
  --signals-dir forward/ZIPING_FWD_001/signals \
  --out-dir forward/ZIPING_FWD_001/status \
  --provider sina \
  --symbol 000001 \
  --start 20260817 \
  --end YYYYMMDD
```

GitHub Actions performs the same process automatically at approximately 08:00 and 16:30 Asia/Shanghai on weekdays.

## Non-goals

- no claim of supernatural causality;
- no live trading recommendation engine at this stage;
- no discretionary post-hoc interpretation;
- no hidden provider switching;
- no LLM-generated daily metaphysical narrative as a feature source;
- no model selection based only on highest historical return;
- no repeated primary-gate testing after failure;
- no hidden rule changes after seeing market outcomes.

## Version

`v0.4.0-alpha` — corrected historical research pipeline plus the first immutable forward-only Ziping candidate test.
