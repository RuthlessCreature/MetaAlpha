# RFC-0009A — First MetaAlpha v2 regime prototype result

Date: 2026-08-18  
Experiment: `META_REGIME_NULL_2025_001`  
Status: **RETROSPECTIVE DIAGNOSTIC / NO PROMOTION**

## 1. Main result

The first market-only regime definition (`ret_lag_20` sign × past-only prior-252-session `vol_lag_20` tercile) did **not** improve the ordinary baseline over 2025-01-02..2026-08-17.

- R0 ordinary baseline LogLoss: `0.692485`
- R1 baseline + market regime LogLoss: `0.694566`
- R0 Brier: `0.249673`
- R1 Brier: `0.250698`

Therefore this specific regime definition is rejected as a superior baseline. Symbolic improvements relative to R1 must not be interpreted without also checking absolute performance versus R0.

## 2. Symbolic results under this regime prototype

### Cycle

- R3 improvement versus R1: `+0.001726` LogLoss, `+0.000883` Brier.
- R3 absolute LogLoss: `0.692839`, still worse than R0 `0.692485`.
- matched shifted-state percentile: `86.1%`, empirical p `0.162`.
- classification: **generic temporal-encoding candidate / no traditional uniqueness**.

A large local gain appeared in `up|low` (`n=107`, ΔLogLoss `+0.01422`), but other regimes were negative and the full mapping failed the matched-null uniqueness rule.

### Ziping

- R2 main-effect improvement versus R1: `+0.001206` LogLoss, `+0.000610` Brier.
- R3 interaction model worsened versus R2 by `-0.000464` LogLoss and `-0.000231` Brier.
- R3 absolute LogLoss: `0.693824`, worse than R0.
- R3 shifted-state percentile: `97.2%`, but empirical p `0.0541` and primary effect thresholds versus R1 were not met.
- classification: **weak historical main-effect candidate; current regime interaction rejected**.

### Qimen

R3 worsened R1 and R2. No promotion.

### Meihua

R2 and R3 materially worsened losses; actual mapping remained at the bottom of the matched-null distribution. `MEIHUA_TIME_V1` remains historical failure.

## 3. Framework implication

The evidence does **not** support simply replacing MetaAlpha v1 with a static market-regime × symbolic interaction model.

Next architecture tests should distinguish:

1. **adaptive routing** — whether past-only recent expert performance can switch among fixed experts without defining regimes by hand (Track T);
2. **better ordinary regime models** — any future regime baseline must beat R0 before symbolic interactions are interpreted;
3. **matched-null uniqueness** — all traditional conditional effects remain required to beat identical-capacity null families;
4. **no natal-anchor rescue** — corrected SSE natal-transit work already rejected unique real-anchor specificity.

## 4. Non-negotiable interpretation rule

If `R1 > R0` in loss (worse), a symbolic model beating R1 is not sufficient. It must also beat R0 and its matched nulls before being considered useful.

This addendum does not alter `META_FWD_001` or any prospective gate.
