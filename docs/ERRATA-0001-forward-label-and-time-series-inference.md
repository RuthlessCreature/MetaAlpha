# ERRATA-0001: Forward-Volatility Label and Time-Series Inference

Date: 2026-08-16  
Severity: **CRITICAL**  
Status: corrected in code; affected research runs require reanalysis

## 1. Summary

Two methodological defects were discovered after the first standalone Ziping and SSE natal-transit historical runs.

### Defect A — forward-volatility label misalignment

The original implementation used:

```python
s.shift(-h).rolling(h, min_periods=h).std().shift(h - 1)
```

For a row at session `t`, this does **not** place the volatility of one-session returns `t+1..t+h` on row `t`. For `h=5`, the resulting window is displaced and can include observations from the present/past side of the intended target.

The correct implementation is equivalent to:

```python
s.rolling(h, min_periods=h).std().shift(-h)
```

which places the standard deviation of exactly `ret_1[t+1], ..., ret_1[t+h]` on row `t`.

A hand-verifiable unit test now constructs known returns of 1%, 2%, 3%, 4%, 5%, 6% and verifies that:

- row 0 `vol_fwd_5` equals `std(1%,2%,3%,4%,5%)`;
- row 1 `vol_fwd_5` equals `std(2%,3%,4%,5%,6%)`.

## 2. Defect B — IID inference on dependent market targets

The original categorical screen used Welch independent-sample t-tests.

That assumption is inappropriate for daily financial time-series targets and is especially inappropriate for overlapping forward windows such as `vol_fwd_5`, where adjacent target rows share future sessions.

The corrected research path uses one-vs-rest OLS with Newey-West/HAC covariance:

- `ret_fwd_1`: HAC maxlags = 5;
- `vol_fwd_5`: HAC maxlags = 20.

Benjamini-Hochberg correction remains applied across the entire registered feature family.

## 3. Partition-boundary leakage

Forward labels are calculated on the complete market series before chronological slicing. Therefore the final `h` rows of any historical partition can use outcomes from the next partition unless explicitly removed.

The corrected pipeline now purges the final target-horizon rows independently per symbol for every partition/era and every walk-forward test block.

## 4. Affected historical conclusions

The following earlier results are **invalidated as statistical evidence** until corrected reruns complete:

- `ZIPING_002` — standalone Ziping → forward five-session volatility;
- `ZIPING_004` — formation/failure/rescue state → forward five-session volatility;
- `SSE_NATAL_002` — natal-transit relations → forward five-session volatility.

The earlier numeric p-values/FDR values for these targets must not be cited as evidence.

Return-target experiments (`ZIPING_001`, `ZIPING_003`, `SSE_NATAL_001`) did not use the broken volatility label, but their earlier IID p-values are also superseded by HAC reanalysis for consistency.

## 5. Corrected research protocol

All corrected reruns must:

1. use the repaired `vol_fwd_h` label;
2. pin the canonical market-data provider;
3. purge target-horizon rows at partition boundaries;
4. use HAC time-series inference;
5. retain family-wide multiple-testing correction;
6. retain shifted/fake controls;
7. label already exposed historical intervals as burned/exploratory rather than creating a fake new holdout.

## 6. Scientific consequence

The previously reported strong natal-transit/volatility association is withdrawn pending corrected analysis.

MetaAlpha treats finding and publishing this error as a successful quality-control outcome. The project objective is falsifiable evidence, not preserving a preferred metaphysical narrative.
