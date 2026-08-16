# Changelog

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
