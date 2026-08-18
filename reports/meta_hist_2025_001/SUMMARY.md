# META_HIST_2025_001 — 2025+ Retrospective Holdout Diagnostic

**Evidence status: RETROSPECTIVE / DESCRIPTIVE ONLY.** The model fit uses only pre-2025 eligible rows, but the symbolic candidate family itself was selected after these historical outcomes existed. Nothing here can alter or rescue `META_FWD_001`.

Training rows: **8,291** (1991-01-18 .. 2024-12-31)
Test rows: **393** (2025-01-02 .. 2026-08-17)
Prediction target: same-session close-to-close direction; 09:25 information convention; all market predictors lagged to information known by t-1 close.

## Full 2025+ metrics

| model_id    |   n |   log_loss |   brier_score |   roc_auc |   accuracy |   calibration_slope |   probability_spread_return |
|-------------|-----|------------|---------------|-----------|------------|---------------------|-----------------------------|
| baseline    | 393 |   0.692936 |      0.249891 |  0.483984 |   0.544529 |          -0.249962  |                 0.000296208 |
| cycle       | 393 |   0.692333 |      0.24958  |  0.505295 |   0.53944  |           0.130098  |                 0.000400177 |
| ziping      | 393 |   0.691768 |      0.249302 |  0.504452 |   0.516539 |           0.0813051 |                 0.00138001  |
| qimen       | 393 |   0.692325 |      0.249572 |  0.501528 |   0.529262 |           0.0455801 |                 0.000568814 |
| meihua      | 393 |   0.697581 |      0.252192 |  0.474316 |   0.501272 |          -0.544182  |                -0.0026591   |
| liuyao_hash | 393 |   0.690655 |      0.24876  |  0.504373 |   0.513995 |           0.277729  |                -0.000133923 |

## Increment versus identical baseline test rows

| model_id    |   negative_control |   logloss_improvement_vs_baseline |   brier_improvement_vs_baseline |   auc_delta_vs_baseline |   accuracy_delta_vs_baseline |   bootstrap_logloss_probability_positive |   bootstrap_brier_probability_positive |
|-------------|--------------------|-----------------------------------|---------------------------------|-------------------------|------------------------------|------------------------------------------|----------------------------------------|
| liuyao_hash |                  1 |                       0.00228146  |                     0.00113132  |              0.0203888  |                  -0.0305344  |                                   0.915  |                                 0.907  |
| ziping      |                  0 |                       0.00116812  |                     0.000589127 |              0.0204678  |                  -0.0279898  |                                   0.811  |                                 0.8215 |
| qimen       |                  0 |                       0.000611021 |                     0.000319562 |              0.0175439  |                  -0.0152672  |                                   0.6575 |                                 0.68   |
| cycle       |                  0 |                       0.000602683 |                     0.000311041 |              0.0213108  |                  -0.00508906 |                                   0.6475 |                                 0.664  |
| meihua      |                  0 |                      -0.00464538  |                    -0.00230139  |             -0.00966756 |                  -0.043257   |                                   0.0355 |                                 0.0315 |

## Frozen C selected using pre-2025 training only

| model_id    |   best_C |   train_n |   test_n |
|-------------|----------|-----------|----------|
| baseline    |     0.01 |      8291 |      393 |
| cycle       |     0.01 |      8291 |      393 |
| ziping      |     0.01 |      8291 |      393 |
| qimen       |     0.01 |      8291 |      393 |
| meihua      |     0.01 |      8291 |      393 |
| liuyao_hash |     0.01 |      8291 |      393 |

## Calendar-year slices

| slice     | model_id    |   n |   log_loss |   brier_score |   roc_auc |   accuracy |
|-----------|-------------|-----|------------|---------------|-----------|------------|
| year_2025 | baseline    | 243 |   0.695253 |      0.251048 |  0.461677 |   0.534979 |
| year_2025 | cycle       | 243 |   0.69163  |      0.249242 |  0.510307 |   0.530864 |
| year_2025 | ziping      | 243 |   0.69565  |      0.251235 |  0.478071 |   0.497942 |
| year_2025 | qimen       | 243 |   0.691239 |      0.249036 |  0.502698 |   0.534979 |
| year_2025 | meihua      | 243 |   0.700193 |      0.253489 |  0.450401 |   0.502058 |
| year_2025 | liuyao_hash | 243 |   0.693263 |      0.250059 |  0.480908 |   0.506173 |
| year_2026 | baseline    | 150 |   0.689183 |      0.248017 |  0.516634 |   0.56     |
| year_2026 | cycle       | 150 |   0.693473 |      0.250128 |  0.497932 |   0.553333 |
| year_2026 | ziping      | 150 |   0.685479 |      0.24617  |  0.546484 |   0.546667 |
| year_2026 | qimen       | 150 |   0.694085 |      0.250439 |  0.498471 |   0.52     |
| year_2026 | meihua      | 150 |   0.693351 |      0.250092 |  0.508362 |   0.5      |
| year_2026 | liuyao_hash | 150 |   0.686428 |      0.246656 |  0.536414 |   0.526667 |

## Interpretation

- Lower LogLoss and Brier are better; positive improvement columns mean the symbolic model beats the ordinary market baseline.
- AUC and accuracy are secondary diagnostics; one historical period is not evidence of causal or metaphysical validity.
- `liuyao_hash` is a deterministic negative control. If it looks as good as or better than traditional branches, that weakens any symbolic interpretation.
- No PASS/FAIL gate is defined for this retrospective experiment.

## Data manifest

```json
{
  "canonical_sha256": "26f48b4a8844ffc93197edb0605cfac508008851a7abf298a41032d848cf460f",
  "fetched_at_utc": "2026-08-18T03:16:52.270092+00:00",
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
