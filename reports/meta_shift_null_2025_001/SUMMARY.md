# META_SHIFT_NULL_2025_001 — Shifted-State Matched Null Diagnostic

**Evidence status: RETROSPECTIVE / DESCRIPTIVE ONLY.**

Train rows: **8,050**; test rows: **393** (2025-01-02 .. 2026-08-17).
Model C fixed at **0.01** for actual and shifted copies. Each branch is compared with **36** trading-session shifts of its own joint state sequence.

Baseline LogLoss: **0.692658**; Brier: **0.249758**.

## Traditional mapping versus its shifted copies

| branch   |   actual_log_loss |   actual_brier_score |   actual_roc_auc |   actual_accuracy |   actual_logloss_improvement_vs_baseline |   actual_brier_improvement_vs_baseline |   shift_null_logloss_mean_improvement |   shift_null_logloss_p95_improvement |   actual_logloss_percentile_vs_shifts |   empirical_logloss_p_one_sided |   shift_null_brier_mean_improvement |   shift_null_brier_p95_improvement |   actual_brier_percentile_vs_shifts |   empirical_brier_p_one_sided |
|----------|-------------------|----------------------|------------------|-------------------|------------------------------------------|----------------------------------------|---------------------------------------|--------------------------------------|---------------------------------------|---------------------------------|-------------------------------------|------------------------------------|-------------------------------------|-------------------------------|
| ziping   |          0.691194 |             0.24903  |         0.504346 |          0.526718 |                              0.00146423  |                            0.000728462 |                          -0.000824    |                           0.00216324 |                              0.861111 |                        0.162162 |                        -0.000405108 |                         0.00107297 |                            0.861111 |                      0.162162 |
| cycle    |          0.691401 |             0.249124 |         0.508667 |          0.536896 |                              0.00125651  |                            0.000634473 |                          -0.000594516 |                           0.00238007 |                              0.777778 |                        0.243243 |                        -0.000288495 |                         0.00119094 |                            0.777778 |                      0.243243 |
| qimen    |          0.691801 |             0.249315 |         0.501502 |          0.516539 |                              0.000856353 |                            0.000442624 |                          -0.00039573  |                           0.00375594 |                              0.722222 |                        0.297297 |                        -0.00019528  |                         0.00185877 |                            0.722222 |                      0.297297 |
| meihua   |          0.69761  |             0.252208 |         0.471471 |          0.506361 |                             -0.00495198  |                           -0.00244953  |                          -8.08065e-05 |                           0.00264336 |                              0        |                        1        |                        -3.73755e-05 |                         0.00131727 |                            0        |                      1        |

## Interpretation rule

A branch beating baseline is not sufficient. If its actual date alignment is not near the top of the shifted-state null distribution, the result is compatible with generic temporal partitioning rather than unique information in the traditional mapping.

## Data manifest

```json
{
  "canonical_sha256": "26f48b4a8844ffc93197edb0605cfac508008851a7abf298a41032d848cf460f",
  "fetched_at_utc": "2026-08-18T03:30:17.033626+00:00",
  "first_date": "1990-12-19",
  "last_date": "2026-08-17",
  "requested_end": "20260817",
  "requested_start": "19901219",
  "rows": 8705,
  "source": "AKShare / Sina index history",
  "source_method": "ak.stock_zh_index_daily",
  "source_version": "1.18.84",
  "symbol": "000001"
}
```
