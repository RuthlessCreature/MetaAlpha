# SSE Historical Data Provider Reconciliation — Corrected

Run date: 2026-08-16  
Workflow run: `31939541828`  
Artifact ID: `9261637551`  
Artifact ZIP SHA256: `b74b0a6428afd48b124065c15e76118fb529639221ac8c585cc9dedd0af12729`

## 1. Correction

An earlier provider-comparison implementation calculated one-session returns inside each provider before aligning common dates. Because Tencent omitted 10 sessions present in Sina, this could compare a one-session return from one provider against a multi-session return from the other and manufacture large discrepancies.

The corrected implementation:

1. identifies provider-specific missing dates;
2. inner-joins providers on common dates;
3. sorts the common-date timeline;
4. computes both providers' returns on that identical timeline;
5. reports omissions separately from price disagreement.

The earlier maximum return discrepancy of roughly 13% is therefore invalid and must not be cited.

## 2. Successful providers

### Sina

- rows: 8,704
- first date: 1990-12-19
- last date: 2026-08-14
- SHA256: `697af81a200060d42b04fa7a79b92fb8287e709ae10baf0825ae301fb4af5aa1`

### Tencent

- rows: 8,694
- first date: 1990-12-19
- last date: 2026-08-14
- SHA256: `a54563ec3785b5290f30b5035b08304f1c46ae4acf9ae55c62bc924b2f21a337`

### Eastmoney direct

The pinned Eastmoney-direct provider failed during this reconciliation run. No fallback was allowed for that provider-specific check.

## 3. Sina vs Tencent on 8,694 common dates

| Metric | Result |
|---|---:|
| Sina-only dates | 10 |
| Tencent-only dates | 0 |
| Mean absolute close difference | 0.0027879 points |
| Maximum absolute close difference | 1.92 points |
| Close difference > 0.1 point | 6 dates |
| Close difference > 1 point | 4 dates |
| Return difference > 1 bp | 12 dates |
| Return difference > 10 bp | 4 dates |
| Return difference > 100 bp | 0 dates |
| Maximum one-session return difference | 0.369173% |

## 4. Tencent omissions relative to Sina

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

## 5. Largest aligned return disagreements

The largest corrected discrepancy occurs around 1996-02-12/13 and is associated with a 1.92-point close discrepancy on 1996-02-12. The maximum aligned one-session return difference is approximately 36.9 basis points, not the previously reported multi-percentage-point discrepancy.

## 6. Decision

For corrected MetaAlpha v1 SSE research, the canonical public-provider input is pinned to Sina (`ak.stock_zh_index_daily`, AKShare 1.18.84).

Rationale is data completeness and observed availability during the quality-control exercise, not favorable model performance. Confirmatory research must fail if the pinned provider is unavailable rather than silently switching vendors.
