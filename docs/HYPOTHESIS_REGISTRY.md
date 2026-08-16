# Hypothesis Registry Standard

Every tested idea must exist in `registry/hypotheses.yaml` before result inspection.

## Required fields

```yaml
id: GANZHI_001
version: 1
branch: ganzhi
status: registered
title: Day-branch effect on next-session return
question: Does day branch change the conditional mean of next-session return?
feature_set:
  - ganzhi__v1__day_branch
target: ret_fwd_1
direction: exploratory
registered_at: 2026-08-16
calendar_convention: Asia/Shanghai civil date
controls:
  - control__v1__weekday
  - control__v1__shift_17_day_branch
multiple_testing_family: ganzhi_day_branch_v1
acceptance:
  min_observations_per_level: 100
  require_oos: true
  require_null_advantage: true
notes: null
```

## Rules

1. A material feature-definition change creates a new ID or version.
2. Failed hypotheses are never deleted.
3. Exploratory hypotheses must be explicitly marked exploratory.
4. The hypothesis registry records what was tested, not just what survived.
5. Results must store the Git commit SHA and data snapshot identifier.
6. If a hypothesis was conceived after seeing the same data, mark it `post_hoc: true`; it cannot be treated as confirmatory evidence on that dataset.

## Status values

- `draft`
- `registered`
- `running`
- `accepted`
- `rejected`
- `inconclusive`
- `frozen`

## Why this exists

Without a permanent hypothesis graveyard, repeated testing produces a fake success rate because losing ideas vanish while lucky winners remain visible. MetaAlpha treats that behavior as a research failure, not a cosmetic documentation problem.
