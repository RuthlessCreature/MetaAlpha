# RFC-0005: Canonical SSE Market-Data Provider

Status: **FROZEN FOR CORRECTED V1 RESEARCH**  
Date: 2026-08-16

## 1. Decision

MetaAlpha corrected v1 SSE research pins the primary historical index provider to:

```text
provider key: sina
AKShare method: ak.stock_zh_index_daily
AKShare version: 1.18.84
symbol: sh000001 / normalized INDEX_000001
requested interval: 1990-12-19 through 2026-08-14
```

The provider is selected for data completeness and observed availability during the data-quality exercise, not for favorable research results.

## 2. Evidence from provider reconciliation

On the successful corrected reconciliation run:

- Sina returned 8,704 sessions from 1990-12-19 through 2026-08-14;
- Tencent returned 8,694 sessions over the same endpoint interval and omitted 10 dates present in Sina;
- the pinned Eastmoney-direct request failed during that reconciliation run and therefore could not participate in the same-run pairwise comparison.

Sina vs Tencent on 8,694 common dates after **common-date alignment before return calculation**:

- mean absolute close difference: approximately 0.00279 index points;
- maximum absolute close difference: 1.92 points;
- dates with close difference > 0.1 point: 6;
- dates with close difference > 1 point: 4;
- one-session return difference > 1 bp: 12;
- one-session return difference > 10 bp: 4;
- one-session return difference > 100 bp: 0;
- maximum one-session return difference: approximately 36.9 bp.

Tencent omitted the following 10 dates relative to Sina:

```text
1991-05-09
1991-06-06
1992-02-13
1992-03-04
1992-05-11
1992-06-16
1993-01-05
1993-02-15
1993-04-08
1994-09-28
```

## 3. Why auto fallback is prohibited in confirmatory research

`provider="auto"` remains useful for availability and exploratory tooling, but it can return a different provenance object on different runs.

Confirmatory or corrected-comparison research must therefore:

1. pin a provider before execution;
2. save source method and package version;
3. save normalized row count and date range;
4. save canonical SHA256;
5. fail rather than silently switch provider when the pinned provider is unavailable.

## 4. Canonical v1 dataset fingerprint

The observed Sina normalized history used in prior successful runs has:

```text
rows: 8704
first date: 1990-12-19
last date: 2026-08-14
SHA256: 697af81a200060d42b04fa7a79b92fb8287e709ae10baf0825ae301fb4af5aa1
```

Any corrected v1 run that receives a different hash must preserve the new manifest and flag the difference rather than silently treating it as the same immutable dataset.

## 5. Limitation

Provider agreement is not proof of exchange-official historical truth. It is a reproducibility control. For high-confidence future work, MetaAlpha may ingest an independently archived or exchange-licensed reference dataset and compare it against these public-provider histories.
