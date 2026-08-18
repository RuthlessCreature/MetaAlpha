# RFC-0010 — MetaAlpha v2: Specificity-First Pivot

Status: **DRAFT FOR NEW EXPERIMENT FAMILIES; DOES NOT MODIFY EXISTING FORWARD IDs**  
Date: 2026-08-18

## 1. Why the v1 framing is no longer sufficient

MetaAlpha v1 mainly asked whether a traditional symbolic block improves a market prediction baseline. The accumulated falsification work shows that this is not enough to support a traditional interpretation.

Historical 2025+ diagnostics now show:

- `LIUYAO_HASH_V1`, an explicitly meaningless SHA256 date encoding, beat all traditional v1 branches on fixed-fit LogLoss;
- among 100 independently salted but structurally identical hash encodings, 26% beat the ordinary market baseline on LogLoss and 25% on Brier;
- the frozen `LIUYAO_HASH_V1` happened to land around the 95th percentile of those 100 hash encodings, while an unrelated seed achieved a much larger historical improvement;
- the current Ziping fixed-fit LogLoss improvement is exceeded by about 15/100 of the frozen synthetic hash seeds;
- under every integer 5..252 trading-session displacement of each traditional joint-state path, exact alignment percentiles are only about 88.7% for Cycle, 87.1% for Ziping, 65.7% for Qimen and 0% for `MEIHUA_TIME_V1`;
- cross-index replication of the historically nominated Cycle and Ziping hybrid models was 0/4;
- direct Ganzhi/solar-term volatility associations were often stronger after arbitrary session shifts and reversed across eras;
- the corrected SSE natal-transit experiment did not establish specificity of the real SSE natal anchor against fake/shifted anchors.

Therefore a symbolic model beating a market baseline can arise without the traditional date mapping being unique.

## 2. New core scientific question

The scientific track must no longer begin with:

> Does this traditional method predict the market?

It must begin with:

> Is the exact traditional mapping unusually informative compared with the space of equally complex deterministic time encodings and displaced copies of itself?

Only after alignment specificity is established should predictive utility be promoted.

## 3. Track S — Specificity-first scientific pipeline

For a newly versioned traditional representation `T`, the required sequence is:

### S0. Frozen semantic representation

Define the traditional mapping without market-outcome access. Freeze:

- source texts / school;
- clock and calendar convention;
- exact feature representation;
- any relation or hierarchy rules;
- target and anchor time.

No rule may change after the evaluation sample is opened.

### S1. Ordinary baseline residual

Require `Market + T` to improve a preregistered ordinary market baseline on primary probabilistic losses.

A weak or deliberately damaged ordinary baseline is not acceptable evidence.

### S2. Ordinary-calendar stress

Test whether the gain survives richer non-traditional calendar controls. The rich-calendar model itself need not replace the baseline if it performs worse; this is a stress test, not a mandatory baseline substitution.

### S3. Matched alignment null

Compare the exact traditional alignment with a preregistered matched-null family, including at minimum:

- displaced copies of the same joint state process;
- synthetic deterministic encodings with comparable cardinality/model capacity;
- where relevant, fake anchors or phase scrambles that preserve persistence structure.

The inference unit is the **whole candidate mapping**, not the most favorable category inside it.

### S4. Global selection-aware null

If several traditional branches or representation variants are evaluated, significance must be assessed against the best result produced by the entire frozen null/candidate search family, not with branch-by-branch unadjusted thresholds.

For new v2 families, prefer a max-statistic / Westfall-Young-style or equivalent familywise null procedure over interpreting individual historical ranks.

### S5. Temporal invariance

Require evidence across preregistered chronological windows. Sign reversals or isolated regime wins are descriptive diagnostics, not a stable factor.

### S6. External market replication

A general claim requires replication on markets not used for representation or model selection. Otherwise the claim must explicitly remain market-specific.

### S7. Prospective immutable confirmation

Only a newly registered future-only experiment may promote a historical survivor. Historical specificity is a nomination criterion, never final validation.

## 4. Track T — Trading utility without traditional claims

A separate trading track may use any deterministic time encoding if it improves future prediction, including:

- synthetic hash encodings;
- Fourier/calendar phases;
- residue classes;
- traditional mappings;
- ensembles of frozen random temporal features.

But Track T must prohibit post-hoc seed picking. If random features are used, the seed family and aggregation rule must be frozen before the target period. A lucky single seed selected after historical inspection is invalid.

Track T conclusions are strictly predictive:

> this frozen temporal encoding/ensemble improves future probability quality.

They are never evidence for metaphysical or traditional validity.

## 5. What current v1 branches become under v2

| Branch | Historical v2 status |
|---|---|
| `MEIHUA_TIME_V1` | historical failure; no in-place rescue |
| Qimen v1 market block | unstable / no specificity |
| Cycle v1 | generic temporal-encoding candidate, not traditional-specific |
| current structural Ziping block | weak residual candidate, exact alignment specificity not established |
| `LIUYAO_HASH_V1` | lucky-looking negative control / generic temporal-encoding benchmark |

These are historical classifications only. `META_FWD_001` continues unchanged so that its already-frozen prospective evidence remains valid.

## 6. Immediate stop rule

Until the already launched daily-expanding reconstructions are recorded, do not create new symbolic feature versions. In particular, do not rescue historical failures by adding Shensha, Nayin, alternative Meihua scoring, new Qimen mappings, or post-hoc Ziping rules.

## 7. Implication

MetaAlpha v2 is no longer a tournament of metaphysical schools.

It is a falsification framework for a stronger claim:

> **Does an exact traditional temporal mapping contain alignment-specific information that cannot be reproduced by ordinary calendar structure, displaced copies, synthetic encodings, selection effects, market-specific anomalies, or regime coincidence?**

If the answer is no, the scientific claim fails even if a trading model built from the encoding happens to work.

If the answer is yes historically, the result still requires independent and prospective confirmation.
