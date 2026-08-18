# RFC-0009 — MetaAlpha v2: regime-conditioned symbolic testing and matched null benchmarks

Status: **DRAFT / NOT ACTIVE / MUST NOT ALTER META_FWD_001**  
Date: 2026-08-18

## 1. Why a redesign is being considered

The current research program has produced three uncomfortable but useful observations:

1. historical symbolic effects are strongly regime-dependent;
2. exact cross-index replication of earlier Shanghai cycle/Ziping winners failed 0/4;
3. in the 2025+ retrospective fixed-fit diagnostic, the deterministic hash-derived six-line negative control achieved better full-period LogLoss than every traditional branch.

These observations make a simple question such as “which school is best?” scientifically inadequate. A symbolic date mapping may look useful merely because it partitions time into categories that accidentally line up with market regimes. The next framework must therefore distinguish **special information in the traditional mapping** from **generic information available to arbitrary deterministic time partitions**.

## 2. Split the project into two questions

### Track S — scientific uniqueness

Question:

> Does a registered traditional mapping contain incremental information beyond ordinary market factors **and beyond matched arbitrary time encodings with similar complexity and persistence**?

A traditional branch cannot be called special merely because it beats the ordinary baseline. It must also beat an empirical null family.

### Track T — trading utility

Question:

> Can any deterministic time-state representation improve market forecasting out of sample, regardless of whether the representation is traditional, synthetic, or arbitrary?

A synthetic/hash representation may be useful here, but success on Track T is **not** evidence for metaphysical validity.

The two tracks must never share language such as “validated metaphysical factor” unless Track S passes.

## 3. Replace one negative control with a matched null family

`LIUYAO_HASH_V1` is useful but one control is insufficient. MetaAlpha v2 should register a finite null ensemble before evaluation.

Suggested null classes:

1. **Cardinality-matched hashes** — same number of categorical levels as each symbolic block.
2. **Persistence-matched Markov controls** — synthetic states with approximately the same transition frequency / dwell-time distribution as the traditional state.
3. **Shifted mappings** — deterministic +17/+31/+47 trading-session or civil-day shifts where meaningful.
4. **Label permutations within calendar strata** — preserve weekday/month seasonality while breaking the traditional mapping.
5. **Phase-scrambled cyclic controls** — preserve cycle length but randomize phase origin.

For each traditional branch, compare its improvement to the empirical distribution of matched-null improvements. Promotion should require superiority to the null family, not merely superiority to baseline.

## 4. Put market regime before symbolic interpretation

The old architecture effectively asks:

`ordinary market features + symbolic state -> direction probability`

MetaAlpha v2 should explicitly model:

`ordinary market regime -> baseline probability`

then ask whether:

`symbolic state | ordinary regime`

adds information.

Regime definitions must be created from ordinary market data only and frozen before symbolic interaction tests. Candidate regime variables may include:

- 20/60/120-day trend state;
- realized-volatility quantile;
- drawdown state;
- overnight-gap regime;
- volume/liquidity regime;
- bull / neutral / bear state from a mechanical rule;
- optional cross-sectional breadth if point-in-time breadth data are added later.

No symbolic feature may participate in defining the regime.

## 5. Test interactions, not only main effects

A branch that alternates between useful and harmful across years may have near-zero unconditional value but non-zero conditional value.

Registered model ladder:

- `R0`: ordinary baseline;
- `R1`: ordinary baseline + ordinary regime indicators;
- `R2`: R1 + symbolic main effects;
- `R3`: R1 + symbolic × regime interactions;
- `N2/N3`: matched-null analogues with identical model capacity.

The key scientific contrast is not only `R3 - R1`; it is also:

`R3 improvement percentile within matched N3 null family`.

## 6. Control sparse-category overfitting

One-hot ridge logistic remains a useful transparent baseline, but high-cardinality symbolic states can create accidental partitions. v2 should evaluate a pre-registered shrinkage ladder:

1. ridge one-hot logistic;
2. frequency / cardinality-capped representation;
3. hierarchical or partial-pooling categorical model if practical;
4. no nonlinear tree model unless separately registered before seeing the new holdout.

Any increase in model capacity must be mirrored in the matched-null family.

## 7. Regime stability is a first-class endpoint

For each branch report:

- full-sample ΔLogLoss / ΔBrier;
- calendar-year signs;
- 20/60/120-session rolling improvement;
- regime-specific improvement;
- number of sign reversals;
- fraction of months beating baseline;
- fraction of months beating the best matched null;
- worst-regime performance;
- cross-index replication where data permit.

A branch with strong mean improvement but repeated sign reversals should be treated as a conditional/regime candidate, not a universal factor.

## 8. Optional online router belongs to Track T only

If the goal is trading utility, a separately registered online expert router can allocate weight among baseline, traditional branches and synthetic controls using **past-only** performance (for example exponential weighting / Hedge).

Rules:

- all experts fixed before start;
- weight updates use only realized prior sessions;
- synthetic controls remain eligible experts;
- router success means “adaptive deterministic time-state ensemble works,” not “traditional metaphysics validated.”

A router must receive its own hypothesis ID and forward holdout.

## 9. Promotion standard for a traditional branch under v2

A candidate traditional branch should require all of the following before being described as uniquely informative:

1. positive incremental primary-loss improvement over ordinary baseline;
2. temporal stability under a frozen rule;
3. acceptable cross-market replication or an explicitly market-specific claim;
4. matched-null empirical percentile above a pre-registered threshold (suggested >=95th percentile);
5. no negative-control family alarm;
6. future-only confirmation under a new hypothesis ID.

## 10. What this RFC does not do

This RFC does not:

- modify `META_FWD_001`;
- reinterpret prior failures;
- promote any branch;
- define a new active trading system;
- allow post-hoc changes to Meihua, Qimen, Ziping or Cycle rules.

The immediate next evidence source is `META_HIST_EXPANDING_2025_001`. Its rolling/regime diagnostics should be used to decide whether this draft is worth turning into a preregistered v2 experiment.
