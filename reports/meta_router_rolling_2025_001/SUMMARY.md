# META_ROUTER_ROLLING_2025_001 — Rolling-window online routers

**RETROSPECTIVE / TRACK T ONLY.**

Every session uses only expert losses realized before that session. Windows 20/60/120 are all reported; none is selected as confirmatory.

## Full-period metrics

| model_id                      |   n |   log_loss |   brier_score |   roc_auc |   accuracy |
|-------------------------------|-----|------------|---------------|-----------|------------|
| liuyao_hash                   | 393 |   0.690655 |      0.24876  |  0.504373 |   0.513995 |
| ziping                        | 393 |   0.691768 |      0.249302 |  0.504452 |   0.516539 |
| rolling_hedge_all_20          | 393 |   0.692181 |      0.249511 |  0.495258 |   0.549618 |
| rolling_hedge_all_120         | 393 |   0.692185 |      0.249513 |  0.495206 |   0.549618 |
| rolling_hedge_all_60          | 393 |   0.692189 |      0.249515 |  0.494942 |   0.552163 |
| qimen                         | 393 |   0.692325 |      0.249572 |  0.501528 |   0.529262 |
| cycle                         | 393 |   0.692333 |      0.24958  |  0.505295 |   0.53944  |
| rolling_hedge_traditional_60  | 393 |   0.692651 |      0.249743 |  0.49352  |   0.544529 |
| rolling_hedge_traditional_20  | 393 |   0.692652 |      0.249743 |  0.493546 |   0.544529 |
| rolling_hedge_traditional_120 | 393 |   0.692655 |      0.249745 |  0.493599 |   0.544529 |
| baseline                      | 393 |   0.692936 |      0.249891 |  0.483984 |   0.544529 |
| meihua                        | 393 |   0.697581 |      0.252192 |  0.474316 |   0.501272 |

## Calendar-year metrics

|   year | model_id                      |   n |   log_loss |   brier_score |   roc_auc |   accuracy |
|--------|-------------------------------|-----|------------|---------------|-----------|------------|
|   2025 | baseline                      | 243 |   0.695253 |      0.251048 |  0.461677 |   0.534979 |
|   2025 | rolling_hedge_all_120         | 243 |   0.693778 |      0.25031  |  0.478971 |   0.539095 |
|   2025 | rolling_hedge_all_20          | 243 |   0.693763 |      0.250302 |  0.479317 |   0.539095 |
|   2025 | rolling_hedge_all_60          | 243 |   0.693776 |      0.250309 |  0.47904  |   0.54321  |
|   2025 | rolling_hedge_traditional_120 | 243 |   0.694032 |      0.250434 |  0.480977 |   0.534979 |
|   2025 | rolling_hedge_traditional_20  | 243 |   0.694043 |      0.25044  |  0.480769 |   0.534979 |
|   2025 | rolling_hedge_traditional_60  | 243 |   0.694032 |      0.250435 |  0.480838 |   0.534979 |
|   2026 | baseline                      | 150 |   0.689183 |      0.248017 |  0.516634 |   0.56     |
|   2026 | rolling_hedge_all_120         | 150 |   0.689606 |      0.248222 |  0.521309 |   0.566667 |
|   2026 | rolling_hedge_all_20          | 150 |   0.689617 |      0.248228 |  0.521669 |   0.566667 |
|   2026 | rolling_hedge_all_60          | 150 |   0.689618 |      0.248228 |  0.521309 |   0.566667 |
|   2026 | rolling_hedge_traditional_120 | 150 |   0.690424 |      0.248628 |  0.514656 |   0.56     |
|   2026 | rolling_hedge_traditional_20  | 150 |   0.690398 |      0.248615 |  0.514656 |   0.56     |
|   2026 | rolling_hedge_traditional_60  | 150 |   0.690412 |      0.248622 |  0.514835 |   0.56     |

## Weight diagnostics

| router_id                     | expert      |   ending_weight |   max_weight |   min_weight |
|-------------------------------|-------------|-----------------|--------------|--------------|
| rolling_hedge_all_120         | baseline    |        0.168853 |     0.173993 |     0.161067 |
| rolling_hedge_all_120         | cycle       |        0.160174 |     0.1819   |     0.149776 |
| rolling_hedge_all_120         | ziping      |        0.176639 |     0.179525 |     0.16171  |
| rolling_hedge_all_120         | qimen       |        0.16245  |     0.177772 |     0.159445 |
| rolling_hedge_all_120         | meihua      |        0.157005 |     0.174192 |     0.152113 |
| rolling_hedge_all_120         | liuyao_hash |        0.174878 |     0.181977 |     0.156971 |
| rolling_hedge_all_20          | baseline    |        0.167579 |     0.173377 |     0.160382 |
| rolling_hedge_all_20          | cycle       |        0.17355  |     0.192007 |     0.148028 |
| rolling_hedge_all_20          | ziping      |        0.166203 |     0.184454 |     0.1578   |
| rolling_hedge_all_20          | qimen       |        0.165392 |     0.182674 |     0.154069 |
| rolling_hedge_all_20          | meihua      |        0.159507 |     0.178342 |     0.14698  |
| rolling_hedge_all_20          | liuyao_hash |        0.167769 |     0.183043 |     0.152496 |
| rolling_hedge_all_60          | baseline    |        0.167158 |     0.173993 |     0.159678 |
| rolling_hedge_all_60          | cycle       |        0.164786 |     0.184849 |     0.149776 |
| rolling_hedge_all_60          | ziping      |        0.171554 |     0.182467 |     0.159032 |
| rolling_hedge_all_60          | qimen       |        0.167759 |     0.180112 |     0.155593 |
| rolling_hedge_all_60          | meihua      |        0.1591   |     0.174192 |     0.149747 |
| rolling_hedge_all_60          | liuyao_hash |        0.169643 |     0.180555 |     0.156971 |
| rolling_hedge_traditional_120 | baseline    |        0.204405 |     0.207543 |     0.193494 |
| rolling_hedge_traditional_120 | cycle       |        0.194434 |     0.218083 |     0.18247  |
| rolling_hedge_traditional_120 | ziping      |        0.213326 |     0.216172 |     0.195146 |
| rolling_hedge_traditional_120 | qimen       |        0.197051 |     0.211299 |     0.193004 |
| rolling_hedge_traditional_120 | meihua      |        0.190785 |     0.20827  |     0.18547  |
| rolling_hedge_traditional_120 | liuyao_hash |      nan        |   nan        |   nan        |
| rolling_hedge_traditional_20  | baseline    |        0.201294 |     0.207543 |     0.190524 |
| rolling_hedge_traditional_20  | cycle       |        0.208084 |     0.227937 |     0.179706 |
| rolling_hedge_traditional_20  | ziping      |        0.199726 |     0.220799 |     0.189333 |
| rolling_hedge_traditional_20  | qimen       |        0.198803 |     0.215939 |     0.185767 |
| rolling_hedge_traditional_20  | meihua      |        0.192092 |     0.212552 |     0.177809 |
| rolling_hedge_traditional_20  | liuyao_hash |      nan        |   nan        |   nan        |
| rolling_hedge_traditional_60  | baseline    |        0.201243 |     0.207543 |     0.190898 |
| rolling_hedge_traditional_60  | cycle       |        0.198535 |     0.220411 |     0.18247  |
| rolling_hedge_traditional_60  | ziping      |        0.206255 |     0.218162 |     0.190709 |
| rolling_hedge_traditional_60  | qimen       |        0.201929 |     0.21502  |     0.187251 |
| rolling_hedge_traditional_60  | meihua      |        0.192038 |     0.20827  |     0.181378 |
| rolling_hedge_traditional_60  | liuyao_hash |      nan        |   nan        |   nan        |

Interpretation: a rolling router that improves both 2025 and 2026 would support the hypothesis that the expert edge is time-varying and needs forgetting. It remains a trading-utility result, not traditional uniqueness evidence.
