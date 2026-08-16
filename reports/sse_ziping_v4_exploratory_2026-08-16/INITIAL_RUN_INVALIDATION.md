# ZIPING_V4_001 — Initial Run Invalidation Notice

Run date: 2026-08-16  
Initial workflow run: `31946158306`  
Commit evaluated: `400b70fd7d70298c35d667c46021b46c26e632ef`  
Artifact ID: `9263336331`  
Artifact ZIP SHA256: `c168dbcd8a27b2389fdd121647743ccf0c67b8826e93c65ecf6644c53d0f2c99`

## Status

**INVALIDATED FOR INFERENTIAL USE.**

The workflow executed successfully and the generated dataset remains useful for audit and debugging, but the initial v4 p-values/FDR table must not be treated as a valid research result.

## Reason

The registered v4 feature `zpzt_route__v4__route_state` was tested while the frozen regression baseline already contained `zpzt_route__v3__route_state` fixed effects.

Because v4 route state is a deterministic refinement of the v3 route state, its categorical dummy block can be structurally collinear with the baseline in an era. The initial runner detected a deficient design rank but still fitted/reported the joint test and included the row in the family correction.

Symptoms in the initial artifact included:

- one rank-deficient registered test in every descriptive era;
- impossible coefficient magnitudes around `10^14` to `10^15` basis points in some eras;
- Statsmodels warnings that the covariance of joint constraints was not full rank.

Those values are numerical-identifiability failures, not economic or symbolic effects.

## Correction rule

The registered feature definitions, data provider, baseline covariates, HAC lag, rare-level rule and historical eras are **not changed**.

The corrected runner adds an inference-validity gate:

1. the full design matrix must have full column rank;
2. the HAC covariance submatrix for the tested feature-dummy block must have full rank;
3. if either condition fails, the test is retained as an audit row with `valid_inference=0`, an explicit reason, and `p_value=NaN`;
4. invalid tests are excluded from Benjamini-Hochberg FDR and from diagnostic beta/effect maxima;
5. invalid feature-level coefficients are not emitted as interpretable estimates.

The corrected run remains **exploratory reanalysis**, because the historical outcomes have already been observed. This correction does not restore an unseen holdout.

## Preliminary diagnostic observation from the invalidated artifact

Even before the inference-QC correction, the source-defined position variables themselves did not reproduce the earlier v3 unresolved-position anomaly in 2005-2014:

- `wealth_resource_position_resolution`: raw p ≈ `0.800`;
- `resolved_from_position_count`: raw p ≈ `0.380`;
- `route_blocked_count`: raw p ≈ `0.117`.

Therefore the earlier v3 association attached to the coarse `requires_position_route_count` bucket should not be interpreted as evidence for the classical 财印 position rule. The corrected v4 run is required for the formal family-level decision.
