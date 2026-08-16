# SSE Standalone Ziping v1 — Corrected Reanalysis

Run date: 2026-08-16  
Workflow run: `31939806826`  
Commit evaluated: `446c96b4950b1ac590c01643e9d714f5a3225dd2`  
Artifact ID: `9261707465`  
Artifact ZIP SHA256: `d4cdf9fa96ae55a76d40cd0edaeec8ca39f93665ac4129ecb32c7e2dd7b19103`

## 1. Status

This reanalysis supersedes the inferential interpretation of the original standalone-Ziping run.

Corrections applied:

- `vol_fwd_h` uses exactly future one-session returns `t+1..t+h`;
- chronological partition tails are purged by target horizon;
- one-vs-rest inference uses OLS with Newey-West/HAC covariance;
- the canonical market-data provider is pinned to Sina;
- Benjamini-Hochberg FDR remains applied across the entire registered feature family.

The 2021+ interval was already exposed in the earlier run and remains **burned**. Correcting the methodology does not make it a new holdout.

## 2. Data provenance

- provider: Sina via `ak.stock_zh_index_daily`;
- AKShare version: `1.18.84`;
- symbol: `000001`;
- first date: `1990-12-19`;
- last date: `2026-08-14`;
- rows: `8,704`;
- canonical SHA256: `697af81a200060d42b04fa7a79b92fb8287e709ae10baf0825ae301fb4af5aa1`.

## 3. Corrected diagnostic minima

| Hypothesis | Partition | Registered family FDR | Shift-null family FDR | Decision |
|---|---|---:|---:|---|
| ZIPING_001 | development | 0.1895 | 0.3218 | no evidence |
| ZIPING_001 | validation | 0.4825 | 0.0717 | no evidence |
| ZIPING_001 | burned 2021+ | **0.0367** | 0.8901 | post-hoc forward candidate only |
| ZIPING_002 | development | 0.5464 | 0.9869 | rejected |
| ZIPING_002 | validation | 0.9696 | 0.9664 | rejected |
| ZIPING_002 | burned 2021+ | 0.5377 | 0.7799 | rejected |
| ZIPING_003 | development | 0.8918 | 0.6028 | rejected |
| ZIPING_003 | validation | 0.4725 | 0.5203 | rejected |
| ZIPING_003 | burned 2021+ | 0.1693 | 0.8034 | rejected |
| ZIPING_004 | development | 0.4510 | 0.9105 | rejected |
| ZIPING_004 | validation | 0.1095 | 0.7659 | rejected |
| ZIPING_004 | burned 2021+ | 0.5389 | 0.3388 | rejected |

## 4. ZIPING_001 — the only surviving historical anomaly

Inside the already-burned 2021+ interval, the strongest corrected level is:

```text
feature: zpzt__v1__month_primary_ten_god
level: 偏财
n: 138
mean next-session return: +0.26713%
rest mean: -0.01534%
standardized effect: +0.28517
HAC t-stat: 3.1812
raw p-value: 0.0014667
family BH-FDR: 0.0366663
HAC maxlags: 5
```

This is a statistically interesting historical anomaly under the corrected procedure, but it is **not confirmatory evidence** because:

1. the 2021+ interval had already been inspected before the corrected methodology was frozen;
2. the effect does not pass the same family gate in development or validation;
3. selecting this level after viewing the burned interval makes it a post-hoc candidate.

The only legitimate use of this observation is to freeze an exact forward-only hypothesis before new market outcomes arrive.

## 5. ZIPING_002 and ZIPING_004 — volatility claims withdrawn

With the corrected future-volatility label and HAC inference, neither structural routes nor provisional formation/failure/rescue states survive family-wide multiple-testing correction in any partition.

The previously reported large volatility significance was produced under a misaligned target and inappropriate IID inference and is therefore invalidated.

**Decision: rejected for v1.**

## 6. ZIPING_003 — formation/failure/rescue and next-session return

No partition survives family-wide FDR after HAC correction.

**Decision: rejected for v1.**

## 7. Scientific conclusion

The corrected standalone-Ziping experiment does not support a broad claim that the registered v1 Ziping Zhenquan state system predicts Shanghai Composite daily returns or five-session volatility.

One burned-period anomaly — `month_primary_ten_god == 偏财` and next-session return — is sufficiently specific to justify a new forward-only test, but it must not be backfilled into a historical success claim.
