# META_CALENDAR_STRESS_2025_001 — Rich Gregorian calendar stress test

**RETROSPECTIVE / DESCRIPTIVE ONLY.**

Train rows: **8,291**; test rows: **393** (2025-01-02 .. 2026-08-17).
All calendar controls are deterministic from the target civil date and known before 09:25.

## Full-period metrics

| model_id                       |   n |   log_loss |   brier_score |   roc_auc |   accuracy |   best_C |
|--------------------------------|-----|------------|---------------|-----------|------------|----------|
| rich_calendar_plus_liuyao_hash | 393 |   0.691294 |      0.249081 |  0.507955 |   0.526718 |     0.01 |
| rich_calendar_plus_ziping      | 393 |   0.692419 |      0.249625 |  0.505058 |   0.519084 |     0.01 |
| market_baseline                | 393 |   0.692936 |      0.249891 |  0.483984 |   0.544529 |     0.01 |
| rich_calendar_plus_qimen       | 393 |   0.693284 |      0.250039 |  0.497577 |   0.536896 |     0.01 |
| rich_calendar                  | 393 |   0.693622 |      0.250232 |  0.493072 |   0.521628 |     0.01 |
| rich_calendar_plus_cycle       | 393 |   0.693971 |      0.250383 |  0.50245  |   0.526718 |     0.01 |
| rich_calendar_plus_meihua      | 393 |   0.698187 |      0.25247  |  0.483009 |   0.516539 |     0.01 |

## Increment beyond rich Gregorian calendar baseline

| branch      |   negative_control |   logloss_improvement_vs_rich_calendar |   brier_improvement_vs_rich_calendar |   auc_delta_vs_rich_calendar |   accuracy_delta_vs_rich_calendar |   best_C |
|-------------|--------------------|----------------------------------------|--------------------------------------|------------------------------|-----------------------------------|----------|
| liuyao_hash |                  1 |                            0.00232798  |                          0.00115017  |                    0.0148833 |                        0.00508906 |     0.01 |
| ziping      |                  0 |                            0.00120285  |                          0.000606419 |                    0.0119857 |                       -0.00254453 |     0.01 |
| qimen       |                  0 |                            0.000338402 |                          0.000192438 |                    0.0045045 |                        0.0152672  |     0.01 |
| cycle       |                  0 |                           -0.000349135 |                         -0.000151836 |                    0.0093778 |                        0.00508906 |     0.01 |
| meihua      |                  0 |                           -0.00456458  |                         -0.00223842  |                   -0.0100627 |                       -0.00508906 |     0.01 |

## Calendar-year metrics

|   year | model_id                       |   n |   log_loss |   brier_score |   roc_auc |   accuracy |
|--------|--------------------------------|-----|------------|---------------|-----------|------------|
|   2025 | market_baseline                | 243 |   0.695253 |      0.251048 |  0.461677 |   0.534979 |
|   2025 | rich_calendar                  | 243 |   0.694494 |      0.25067  |  0.478348 |   0.522634 |
|   2025 | rich_calendar_plus_cycle       | 243 |   0.692858 |      0.249845 |  0.505672 |   0.526749 |
|   2025 | rich_calendar_plus_ziping      | 243 |   0.694861 |      0.250852 |  0.482775 |   0.497942 |
|   2025 | rich_calendar_plus_qimen       | 243 |   0.690948 |      0.248898 |  0.500069 |   0.539095 |
|   2025 | rich_calendar_plus_meihua      | 243 |   0.699131 |      0.252931 |  0.4715   |   0.514403 |
|   2025 | rich_calendar_plus_liuyao_hash | 243 |   0.69237  |      0.24962  |  0.493082 |   0.518519 |
|   2026 | market_baseline                | 150 |   0.689183 |      0.248017 |  0.516634 |   0.56     |
|   2026 | rich_calendar                  | 150 |   0.692211 |      0.249521 |  0.514296 |   0.52     |
|   2026 | rich_calendar_plus_cycle       | 150 |   0.695775 |      0.251256 |  0.496673 |   0.526667 |
|   2026 | rich_calendar_plus_ziping      | 150 |   0.688464 |      0.247638 |  0.543607 |   0.553333 |
|   2026 | rich_calendar_plus_qimen       | 150 |   0.697068 |      0.251887 |  0.491458 |   0.533333 |
|   2026 | rich_calendar_plus_meihua      | 150 |   0.696657 |      0.251724 |  0.497932 |   0.52     |
|   2026 | rich_calendar_plus_liuyao_hash | 150 |   0.689552 |      0.248209 |  0.527423 |   0.54     |

Interpretation: if symbolic/hash gains shrink materially versus the richer ordinary-calendar baseline, earlier gains are compatible with generic calendar partitioning. Persistence of a traditional gain still does not establish uniqueness without matched-null tests.
