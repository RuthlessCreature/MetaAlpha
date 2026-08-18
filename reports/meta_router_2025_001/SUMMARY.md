# META_ROUTER_2025_001 — Past-only online expert router

**RETROSPECTIVE / TRACK T ONLY. Not evidence for metaphysical validity.**

Routers use equal initial weights. Session t uses weights available before t; only after t settles are weights updated using expert Brier losses. Learning rate is parameter-free `sqrt(2 ln K / t)`.

## Full-period metrics

| model_id             |   n |   log_loss |   brier_score |   roc_auc |   accuracy |
|----------------------|-----|------------|---------------|-----------|------------|
| liuyao_hash          | 393 |   0.690655 |      0.24876  |  0.504373 |   0.513995 |
| ziping               | 393 |   0.691768 |      0.249302 |  0.504452 |   0.516539 |
| hedge_all_v1         | 393 |   0.692196 |      0.249518 |  0.494758 |   0.552163 |
| qimen                | 393 |   0.692325 |      0.249572 |  0.501528 |   0.529262 |
| cycle                | 393 |   0.692333 |      0.24958  |  0.505295 |   0.53944  |
| hedge_traditional_v1 | 393 |   0.69264  |      0.249737 |  0.493704 |   0.549618 |
| baseline             | 393 |   0.692936 |      0.249891 |  0.483984 |   0.544529 |
| meihua               | 393 |   0.697581 |      0.252192 |  0.474316 |   0.501272 |

## Router calendar-year metrics

|   year | model_id             |   n |   log_loss |   brier_score |   roc_auc |   accuracy |
|--------|----------------------|-----|------------|---------------|-----------|------------|
|   2025 | baseline             | 243 |   0.695253 |      0.251048 |  0.461677 |   0.534979 |
|   2025 | hedge_all_v1         | 243 |   0.693835 |      0.250338 |  0.478556 |   0.54321  |
|   2025 | hedge_traditional_v1 | 243 |   0.694073 |      0.250455 |  0.4807   |   0.530864 |
|   2026 | baseline             | 150 |   0.689183 |      0.248017 |  0.516634 |   0.56     |
|   2026 | hedge_all_v1         | 150 |   0.689541 |      0.24819  |  0.521129 |   0.566667 |
|   2026 | hedge_traditional_v1 | 150 |   0.690318 |      0.248575 |  0.516094 |   0.58     |

## Router weight diagnostics

| router_id            | expert      |   ending_weight |   max_weight |   min_weight |
|----------------------|-------------|-----------------|--------------|--------------|
| hedge_all_v1         | baseline    |        0.176194 |     0.183014 |     0.166667 |
| hedge_all_v1         | cycle       |        0.158547 |     0.166667 |     0.14343  |
| hedge_all_v1         | ziping      |        0.17625  |     0.177947 |     0.166667 |
| hedge_all_v1         | qimen       |        0.17429  |     0.180089 |     0.160693 |
| hedge_all_v1         | meihua      |        0.141579 |     0.172476 |     0.140866 |
| hedge_all_v1         | liuyao_hash |        0.17314  |     0.180683 |     0.158536 |
| hedge_traditional_v1 | baseline    |        0.21242  |     0.217871 |     0.2      |
| hedge_traditional_v1 | cycle       |        0.192202 |     0.2      |     0.175864 |
| hedge_traditional_v1 | ziping      |        0.212484 |     0.213716 |     0.2      |
| hedge_traditional_v1 | qimen       |        0.210244 |     0.214999 |     0.194364 |
| hedge_traditional_v1 | meihua      |        0.17265  |     0.208115 |     0.171711 |

Interpretation: if the all-expert router wins while allocating material weight to synthetic/hash experts, that supports adaptive time-encoding utility only. If the traditional-only router wins independently, that is still historical and requires a new future experiment.
