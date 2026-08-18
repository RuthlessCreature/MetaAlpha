# RFC-0011 — Versioned historical market snapshots

Status: **DRAFT / DATA-ENGINEERING POLICY / NO PREDICTOR CHANGE**

## Problem

Historical MetaAlpha experiments currently record provider, version, requested range and canonical SHA256, but many reports do not retain the exact normalized market frame used by the run. A later provider revision can therefore reproduce the manifest schema while producing different historical bytes.

## Proposed policy

For every new retrospective experiment family:

1. fetch the pinned provider exactly once;
2. normalize through the registered MetaAlpha data-normalization path;
3. store the exact normalized frame as a versioned research snapshot or immutable workflow artifact with long retention;
4. store SHA256, row count, first/last date and provider metadata next to it;
5. all parallel workers in the same experiment must consume the same snapshot bytes;
6. reruns intended as exact reproduction must use the frozen snapshot, not silently re-fetch the provider;
7. a refreshed-provider rerun is a separate data-revision sensitivity analysis and must receive a new run ID.

## Scope

This policy is for retrospective research reproducibility. It must not replace the live provider path used by `META_FWD_001`, whose forward evidence requires data actually available to the scheduled process at the time.

## Storage guidance

Prefer compressed CSV or Parquet when repository policy permits. If repository size is a concern, use a long-retention immutable GitHub Actions artifact plus a committed manifest containing the artifact ID/hash. Do not retain only a mutable external URL.
