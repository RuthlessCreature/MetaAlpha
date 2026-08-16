# SUPERSEDED — SSE_NATAL_V1 Historical Exploration

**Do not use the statistical results from this file as evidence.**

The original 2026-08-16 natal-transit run was later found to rely on a misaligned forward-volatility label and IID inference that was inappropriate for dependent financial time-series targets. The run also used a different market-data provider from the canonical corrected v1 input.

The methodology defect and correction protocol are documented in:

- `docs/ERRATA-0001-forward-label-and-time-series-inference.md`
- `docs/RFC-0005-canonical-market-data-provider.md`

The corrected natal-transit result is documented in:

- `reports/sse_natal_corrected_2026-08-16/RESULTS.md`
- `registry/evaluations/2026-08-16-sse-natal-v1-corrected.yaml`

The original run remains available through Git history and its original workflow artifact for auditability, but its old p-values/FDR values are intentionally removed from the active result document to prevent accidental citation.
