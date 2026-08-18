# META_REGIME_NULL_2025_001 — Regime-conditioned symbolic matched-null diagnostic

**RETROSPECTIVE / DESCRIPTIVE ONLY. Does not modify META_FWD_001.**

Common train rows: **8,039**; test rows: **393** (2025-01-02 .. 2026-08-17).
Fixed C: **0.01**. Regime: 20-session trend sign × past-only 252-session volatility tercile.

## Ordinary model ladder

| model_id         |   log_loss |   brier_score |   roc_auc |   accuracy |   calibration_slope |   probability_spread_return |
|------------------|------------|---------------|-----------|------------|---------------------|-----------------------------|
| R0_baseline      |   0.692485 |      0.249673 |  0.485117 |   0.529262 |           -0.149354 |                  0.00045245 |
| R1_market_regime |   0.694566 |      0.250698 |  0.471735 |   0.526718 |           -0.468706 |                 -0.00152922 |

## Traditional R2/R3 versus shifted-state R3 null family

| branch   |   R2_logloss_improvement_vs_R1 |   R3_logloss_improvement_vs_R1 |   R3_minus_R2_logloss_improvement |   R3_brier_improvement_vs_R1 |   R3_logloss_percentile_vs_shift_null |   R3_logloss_empirical_p_one_sided |
|----------|--------------------------------|--------------------------------|-----------------------------------|------------------------------|---------------------------------------|------------------------------------|
| cycle    |                    0.000912131 |                    0.00172645  |                       0.000814323 |                  0.000883442 |                              0.861111 |                          0.162162  |
| ziping   |                    0.00120581  |                    0.000741676 |                      -0.000464137 |                  0.000379552 |                              0.972222 |                          0.0540541 |
| qimen    |                    0.000780546 |                   -0.00145103  |                      -0.00223157  |                 -0.000707534 |                              0.583333 |                          0.432432  |
| meihua   |                   -0.00497656  |                   -0.00641146  |                      -0.0014349   |                 -0.00315774  |                              0        |                          1         |

Interpretation: R2 tests symbolic main effects after market regime; R3 additionally tests regime×symbolic interactions. A positive R3-R2 improvement suggests conditional rather than universal value. Scientific uniqueness additionally requires the actual R3 to sit near the extreme top of its identical-capacity shifted-state null family.

## Regime-specific R3 improvement

| branch   | market_regime_v1   |   n |   R1_log_loss |   R3_log_loss |   R3_logloss_improvement_vs_R1 |   R1_brier_score |   R3_brier_score |   R3_brier_improvement_vs_R1 |
|----------|--------------------|-----|---------------|---------------|--------------------------------|------------------|------------------|------------------------------|
| cycle    | up|low             | 107 |      0.682202 |      0.66798  |                    0.0142215   |         0.244506 |         0.237495 |                  0.00701055  |
| cycle    | down|mid           |  51 |      0.698699 |      0.699138 |                   -0.000438263 |         0.252773 |         0.252987 |                 -0.000214158 |
| cycle    | down|high          |  97 |      0.684739 |      0.686498 |                   -0.00175957  |         0.245872 |         0.246767 |                 -0.000895603 |
| cycle    | up|high            |  36 |      0.69965  |      0.702552 |                   -0.00290239  |         0.25322  |         0.254665 |                 -0.00144421  |
| cycle    | up|mid             |  97 |      0.714016 |      0.720108 |                   -0.00609229  |         0.260351 |         0.263194 |                 -0.00284334  |
| meihua   | down|mid           |  51 |      0.698699 |      0.690509 |                    0.00818992  |         0.252773 |         0.248704 |                  0.00406896  |
| meihua   | down|high          |  97 |      0.684739 |      0.687425 |                   -0.00268611  |         0.245872 |         0.247256 |                 -0.00138391  |
| meihua   | up|low             | 107 |      0.682202 |      0.686943 |                   -0.00474097  |         0.244506 |         0.246874 |                 -0.00236759  |
| meihua   | up|mid             |  97 |      0.714016 |      0.726772 |                   -0.0127565   |         0.260351 |         0.266566 |                 -0.00621545  |
| meihua   | up|high            |  36 |      0.69965  |      0.718242 |                   -0.0185922   |         0.25322  |         0.262301 |                 -0.00908057  |
| qimen    | down|mid           |  51 |      0.698699 |      0.693483 |                    0.00521589  |         0.252773 |         0.250179 |                  0.00259416  |
| qimen    | up|mid             |  97 |      0.714016 |      0.71344  |                    0.000576406 |         0.260351 |         0.260006 |                  0.000344746 |
| qimen    | up|low             | 107 |      0.682202 |      0.68217  |                    3.23901e-05 |         0.244506 |         0.244466 |                  3.99008e-05 |
| qimen    | down|high          |  97 |      0.684739 |      0.688684 |                   -0.00394544  |         0.245872 |         0.247871 |                 -0.00199971  |
| qimen    | up|high            |  36 |      0.69965  |      0.707961 |                   -0.00831149  |         0.25322  |         0.257314 |                 -0.00409395  |
| ziping   | down|mid           |  51 |      0.698699 |      0.690302 |                    0.00839732  |         0.252773 |         0.248571 |                  0.00420165  |
| ziping   | up|low             | 107 |      0.682202 |      0.679044 |                    0.00315828  |         0.244506 |         0.242969 |                  0.00153657  |
| ziping   | down|high          |  97 |      0.684739 |      0.682865 |                    0.0018739   |         0.245872 |         0.24494  |                  0.000931431 |
| ziping   | up|high            |  36 |      0.69965  |      0.701737 |                   -0.00208679  |         0.25322  |         0.254301 |                 -0.00108023  |
| ziping   | up|mid             |  97 |      0.714016 |      0.722263 |                   -0.00824707  |         0.260351 |         0.264362 |                 -0.0040114   |

## Data manifest

```json
{
  "canonical_sha256": "26f48b4a8844ffc93197edb0605cfac508008851a7abf298a41032d848cf460f",
  "fetched_at_utc": "2026-08-18T03:51:04.964318+00:00",
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
