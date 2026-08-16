# SUPERSEDED — SSE Ziping Zhenquan v1 First Run

**Do not use the statistical results from this file as evidence.**

The original 2026-08-16 run was later found to contain two material methodology defects:

1. the forward-volatility label was misaligned and did not represent exactly `t+1..t+h` future returns;
2. IID Welch inference was used for dependent financial time-series targets, including overlapping forward windows.

Chronological partition tails also required target-horizon purging.

The methodology defect and correction protocol are documented in:

- `docs/ERRATA-0001-forward-label-and-time-series-inference.md`

The corrected standalone-Ziping result is documented in:

- `reports/sse_ziping_corrected_2026-08-16/RESULTS.md`
- `registry/evaluations/2026-08-16-sse-ziping-v1-corrected.yaml`

The original GitHub Actions run and artifact identifiers remain available in repository history for auditability, but their old p-values/FDR values are intentionally not repeated here to reduce the risk of accidental citation.
