# Changelog

## 0.4.0-alpha — 2026-08-16

### Added

- `ZIPING_FWD_001`, the first true forward-only Ziping Zhenquan market candidate.
- Immutable daily signal records under `forward/ZIPING_FWD_001/signals/`.
- Automatic eligibility rejection for records generated after the frozen 09:25 Asia/Shanghai anchor.
- Pinned Sina (`ak.stock_zh_index_daily`) scoring provenance for the forward experiment.
- Calendar-adjusted OLS with Newey-West/HAC covariance for the primary forward gate.
- 17/31/47 actual-session shifted-signal null controls.
- One-time gate locking: the first result after sample thresholds are met is immutable and later monitoring cannot reverse it.
- Scheduled GitHub Actions precommit at 08:00 Asia/Shanghai and realized-status scoring at 16:30.
- `metaalpha-ziping-forward` CLI.

### Frozen forward gate

- forward evidence begins: `2026-08-17`;
- feature: `zpzt__v1__month_primary_ten_god`;
- registered level: `偏财`;
- target: `ret_fwd_1`;
- minimum scored sessions: `300`;
- minimum 偏财 signal sessions: `30`;
- minimum calendar-adjusted effect: `+10 bp`;
- one-sided alpha: `0.025`;
- both chronological halves must have positive raw signal-minus-rest differences;
- the registered signal beta must exceed all 17/31/47-session shifted controls.

The first precommitted record is `2026-08-17`; it evaluates to `正印`, therefore `signal=0 / no_call`. It was committed before the future 09:25 anchor and is retained as part of the complete forward sequence.

### Corrected historical evidence

- Earlier `vol_fwd_5` results were invalidated because the prototype label did not strictly use `t+1..t+5` returns.
- Forward-volatility labels now use exactly the future horizon.
- Market time-series inference moved from IID Welch tests to HAC/Newey-West covariance.
- Partition/era tails are purged by target horizon.
- Standalone Ziping risk hypotheses `ZIPING_002` and `ZIPING_004` no longer show the prior apparent volatility signal under the corrected pipeline.
- `ZIPING_003` remains unsupported for next-session return.
- The exposed 2021+ `偏财` anomaly in `ZIPING_001` is nomination-only and may be tested only with future observations.
- `SSE_NATAL_V1` shows no robust next-session-return evidence; historical volatility associations are not natal-anchor-specific because fake anchors and shifted controls can be as strong or stronger.

### Data quality

- Confirmatory research now pins a provider rather than silently switching providers.
- Cross-provider reconciliation aligns common trading dates before comparing returns.
- Sina supplied 8,704 sessions from 1990-12-19 through 2026-08-14; Tencent supplied 8,694 common/near-common sessions and omitted 10 Sina dates in the corrected reconciliation.

## 0.2.0-alpha — 2026-08-16

### Added

- Solar-term-aware Ganzhi engine backed by pinned `lunar_python==1.4.8`.
- A-share research time convention: `Asia/Shanghai`, session anchor `09:25`.
- Ziping Zhenquan (《子平真诠》) RFC with month-command-first methodology.
- Deterministic ten-god engine.
- Registered hidden-stem table and month-command transmission features.
- Pattern candidates for 官、财、印、食神、七杀、伤官、阳刃、建禄月劫.
- 顺用/逆用 structural route flags.
- Month-command 冲、害、破、刑 variables.
- Provisional 成/败/救应 state machine.
- Explicit `requires_strength` marker for classical rules that depend on 身强身弱 or 轻重.
- Non-arbitrary strength primitives: month relation, exact roots, hidden support, visible support/drain counts.
- Ziping feature integration into the research CLI via `--ziping`.
- Unit tests covering upstream calendar reference data, ten gods, pattern candidates, rescue rules and strength primitives.

### Research constraints

- No aggregate strong/weak score is defined in v0.2.
- No post-hoc change to time anchor, hidden-stem ordering or Yang-Blade convention is permitted under the same hypothesis version.
- Full 有情/无情、有力/无力 scoring and position-sensitive transformations remain deferred.
