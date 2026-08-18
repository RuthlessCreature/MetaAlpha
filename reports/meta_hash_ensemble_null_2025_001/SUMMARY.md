# META_HASH_ENSEMBLE_NULL_2025_001 — 100-seed hash negative-control ensemble

**RETROSPECTIVE / NEGATIVE-CONTROL DIAGNOSTIC ONLY.**

Train rows: **8,291**; test rows: **393** (2025-01-02 .. 2026-08-17).
All 100 salts were frozen as seed IDs 0..99. C is fixed at 0.01. Every seed uses the same four-feature representation as LIUYAO_HASH_V1.

## Ensemble summary

|   baseline_log_loss |   baseline_brier_score |   reference_hash_log_loss |   reference_hash_brier_score |   reference_hash_logloss_improvement |   reference_hash_brier_improvement |   seed_count |   fraction_seed_hashes_beating_baseline_logloss |   fraction_seed_hashes_beating_baseline_brier |   mean_seed_logloss_improvement |   median_seed_logloss_improvement |   p95_seed_logloss_improvement |   reference_hash_percentile_vs_100_seeds_logloss |   reference_hash_tail_fraction_vs_100_seeds_logloss |   mean_seed_brier_improvement |   median_seed_brier_improvement |   p95_seed_brier_improvement |   reference_hash_percentile_vs_100_seeds_brier |   reference_hash_tail_fraction_vs_100_seeds_brier |
|---------------------|------------------------|---------------------------|------------------------------|--------------------------------------|------------------------------------|--------------|-------------------------------------------------|-----------------------------------------------|---------------------------------|-----------------------------------|--------------------------------|--------------------------------------------------|-----------------------------------------------------|-------------------------------|---------------------------------|------------------------------|------------------------------------------------|---------------------------------------------------|
|            0.692936 |               0.249891 |                  0.690655 |                      0.24876 |                           0.00228146 |                         0.00113132 |          100 |                                            0.26 |                                          0.25 |                     -0.00110787 |                       -0.00137897 |                     0.00198178 |                                             0.95 |                                           0.0594059 |                  -0.000546662 |                    -0.000671502 |                  0.000996848 |                                           0.95 |                                         0.0594059 |

## Top 20 synthetic hashes by LogLoss improvement

|   seed |   log_loss |   brier_score |   roc_auc |   accuracy |   logloss_improvement_vs_baseline |   brier_improvement_vs_baseline |
|--------|------------|---------------|-----------|------------|-----------------------------------|---------------------------------|
|      4 |   0.687956 |      0.247395 |  0.53248  |   0.549618 |                       0.00498055  |                     0.00249646  |
|     59 |   0.689676 |      0.24827  |  0.517122 |   0.524173 |                       0.00326023  |                     0.00162105  |
|     41 |   0.69044  |      0.248658 |  0.506006 |   0.541985 |                       0.0024963   |                     0.00123263  |
|     87 |   0.690523 |      0.248702 |  0.504267 |   0.529262 |                       0.00241347  |                     0.00118887  |
|     56 |   0.690621 |      0.248737 |  0.508667 |   0.53944  |                       0.00231509  |                     0.00115444  |
|     86 |   0.690972 |      0.248903 |  0.510326 |   0.544529 |                       0.00196424  |                     0.000988554 |
|     57 |   0.691045 |      0.248958 |  0.506533 |   0.516539 |                       0.00189157  |                     0.000933227 |
|     27 |   0.691158 |      0.248997 |  0.515041 |   0.519084 |                       0.0017786   |                     0.000894516 |
|     98 |   0.691246 |      0.249062 |  0.504794 |   0.513995 |                       0.00168973  |                     0.000829055 |
|     24 |   0.691309 |      0.249084 |  0.498999 |   0.521628 |                       0.00162695  |                     0.000807407 |
|     23 |   0.691393 |      0.249144 |  0.495575 |   0.526718 |                       0.00154269  |                     0.000747209 |
|     54 |   0.69141  |      0.249127 |  0.506849 |   0.524173 |                       0.00152575  |                     0.000764551 |
|     19 |   0.691519 |      0.24918  |  0.507982 |   0.541985 |                       0.00141743  |                     0.000711397 |
|     68 |   0.691653 |      0.249231 |  0.510142 |   0.541985 |                       0.00128315  |                     0.000660085 |
|     40 |   0.691711 |      0.249289 |  0.499947 |   0.529262 |                       0.00122504  |                     0.000602113 |
|      6 |   0.692054 |      0.249463 |  0.493151 |   0.529262 |                       0.000882094 |                     0.000427987 |
|      3 |   0.692177 |      0.249535 |  0.485538 |   0.506361 |                       0.000759408 |                     0.000355828 |
|     91 |   0.692438 |      0.249645 |  0.490754 |   0.531807 |                       0.000498237 |                     0.000246528 |
|     34 |   0.69249  |      0.249675 |  0.492703 |   0.513995 |                       0.000446443 |                     0.000216038 |
|     85 |   0.692559 |      0.249703 |  0.488989 |   0.536896 |                       0.000377305 |                     0.000188318 |

Interpretation: if many seeds beat baseline, generic deterministic date partitioning is sufficient to create apparent signal. If the frozen LIUYAO_HASH_V1 is extreme among seeds, its prior win is consistent with a lucky frozen random encoding. Either way this is a negative control, not a divination claim.

## Data manifest

```json
{
  "canonical_sha256": "26f48b4a8844ffc93197edb0605cfac508008851a7abf298a41032d848cf460f",
  "fetched_at_utc": "2026-08-18T04:08:42.878954+00:00",
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
