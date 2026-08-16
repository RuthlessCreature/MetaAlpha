# HYBRID_REPL_001 — Cross-index Replication Results

Run date: 2026-08-16  
Corrected workflow run: `31951599703`  
Commit evaluated: `3ff58bcf3719484b6b535d9016101ebe6c244696`  
Artifact ID: `9264816985`  
Artifact ZIP SHA256: `729097b194bd72827166d4bd9adf629679ec19c2a888877cbec3c6faf014e9e7`

## 1. Executive decision

**HYBRID_REPL_001 fails cross-index replication for both historically nominated models.**

- `cycle`: **0 / 4 indices passed the complete frozen per-index gate** — replication FAIL.
- `ziping`: **0 / 4 indices passed the complete frozen per-index gate** — replication FAIL.

The preregistered replication requirement was at least **3 / 4** passing indices per candidate. Neither candidate passed even one complete per-index gate.

This result materially downgrades the interpretation of the earlier Shanghai Composite `HYBRID_ALPHA_001` PASS. The earlier result remains a valid preregistered historical walk-forward finding on that selection market, but it does **not** generalize under the same frozen algorithm and acceptance criteria to SSE 50, CSI 300, CSI 500, or Shenzhen Component.

No replication rescue is permitted by dropping an index, changing the symbolic feature set, changing the market baseline, switching model family, changing outer windows, or weakening the gate.

## 2. Evidence status

**PREREGISTERED EXTERNAL-INDEX HISTORICAL REPLICATION.**

The symbolic winners (`cycle`, `ziping`), ordinary market baseline, feature lists, ridge-logistic model family, C grid, time-ordered inner tuning, outer test windows, bootstrap, Holm correction, and 3-of-4 replication gate were frozen before the replication results were inspected.

Shanghai Composite `000001` was deliberately excluded from replication counting because it was the model-selection market in `HYBRID_ALPHA_001`.

The first replication execution (`31951316355`) is not inferential evidence. It stopped before all four indices completed because upstream Sina data contained non-positive volume placeholders. No partial statistical result from that attempt was used. The corrected rerun applied the predeclared QC rule: preserve all OHLC/date rows and return targets, map non-positive volume only to missing for feature construction, never impute the affected frozen volume predictors, and allow the common-row rule to exclude unavailable feature rows.

## 3. Replication markets and data provenance

| Index | Provider symbol | Raw rows | Non-positive volume rows mapped missing | Eligible rows | OOS rows | First date | Last date |
|---|---|---:|---:|---:|---:|---|---|
| SSE 50 | `sh000016` | 5,493 | 0 | 5,472 | 4,035 | 2004-01-02 | 2026-08-14 |
| CSI 300 | `sh000300` | 5,971 | 721 | 5,230 | 4,035 | 2002-01-04 | 2026-08-14 |
| CSI 500 | `sh000905` | 5,250 | 0 | 5,229 | 4,035 | 2005-01-04 | 2026-08-14 |
| Shenzhen Component | `sz399001` | 8,612 | 2 | 8,561 | 4,035 | 1991-04-03 | 2026-08-14 |

Canonical normalized-data SHA256 values:

- SSE 50: `259f6c3e579916602c455cc8c7f51a4decc707b0867ae18c3af0602ecb39e583`
- CSI 300: `b9299dd0fa9c3e5c9245ebbb2e8e310c53856cd62f6f3536cb93dc3081ad493f`
- CSI 500: `00cdefc3ed60b2eec69f5c2139aac09ae107500e288e6af547dd5f8d0724ad95`
- Shenzhen Component: `f3c7b36caf3b91335c8c6768ee31f555790bfb5e016cbbd299a866be7fb63170`

### CSI 300 data-quality note

Sina reports 721 non-positive volume placeholders in the requested CSI 300 history. The frozen QC rule does not alter prices or delete those price dates before target construction. It only makes volume-dependent predictors unavailable on affected feature rows. This materially reduces CSI 300 eligible history, but the same four OOS windows still contain 4,035 comparable test rows.

## 4. Frozen per-index gate results

### SSE 50

| Model | LogLoss improvement | Brier improvement | AUC delta | LL windows won | Brier windows won | Bootstrap P(LL improve) | Bootstrap P(Brier improve) | Holm p LL | Holm p Brier | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| cycle | -0.000155 | -0.000082 | -0.001966 | 2/4 | 2/4 | 0.4115 | 0.3765 | 0.5885 | 0.6235 | FAIL |
| ziping | +0.001093 | +0.000549 | +0.003658 | **4/4** | **4/4** | 0.8970 | 0.9050 | 0.2060 | 0.1900 | FAIL |

`ziping` is directionally interesting on SSE 50 and clears the frozen effect-size/window conditions, but it does not reach the required bootstrap probability or Holm-adjusted significance. It therefore fails by the preregistered rule.

### CSI 300

| Model | LogLoss improvement | Brier improvement | AUC delta | LL windows won | Brier windows won | Bootstrap P(LL improve) | Bootstrap P(Brier improve) | Holm p LL | Holm p Brier | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| cycle | -0.000482 | -0.000222 | -0.001453 | 1/4 | 1/4 | 0.2535 | 0.2520 | 0.9120 | 0.8500 | FAIL |
| ziping | +0.000141 | +0.000103 | +0.003822 | 2/4 | 2/4 | 0.5440 | 0.5750 | 0.9120 | 0.8500 | FAIL |

Neither candidate approaches the complete gate.

### CSI 500

| Model | LogLoss improvement | Brier improvement | AUC delta | LL windows won | Brier windows won | Bootstrap P(LL improve) | Bootstrap P(Brier improve) | Holm p LL | Holm p Brier | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| cycle | **+0.005672** | **+0.002664** | +0.006909 | 2/4 | 2/4 | **1.0000** | **1.0000** | **0.0000** | **0.0000** | FAIL |
| ziping | +0.003067 | +0.001494 | +0.006868 | 2/4 | 2/4 | 0.9715 | 0.9770 | 0.0285 | 0.0230 | FAIL |

CSI 500 contains the strongest aggregate improvements in this replication. Both candidates nevertheless fail because improvement repeats in only **2 of 4** frozen eras. The preregistered temporal-stability condition therefore blocks promotion. This is exactly the type of attractive aggregate result that the multi-era gate was designed not to overinterpret.

### Shenzhen Component

| Model | LogLoss improvement | Brier improvement | AUC delta | LL windows won | Brier windows won | Bootstrap P(LL improve) | Bootstrap P(Brier improve) | Holm p LL | Holm p Brier | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| cycle | -0.001065 | -0.000526 | +0.000438 | 1/4 | 1/4 | 0.0805 | 0.0685 | 1.0000 | 1.0000 | FAIL |
| ziping | -0.000139 | -0.000053 | +0.006079 | 1/4 | 1/4 | 0.4380 | 0.4640 | 1.0000 | 1.0000 | FAIL |

Both candidates fail and have negative aggregate primary-loss improvement.

## 5. Replication decision

| Model | Indices evaluated | Complete per-index gates passed | Required | Replication |
|---|---:|---:|---:|---|
| cycle | 4 | **0** | 3 | **FAIL** |
| ziping | 4 | **0** | 3 | **FAIL** |

## 6. What this falsifies

The corrected result falsifies the strong generalization claim:

> “The exact `HYBRID_ALPHA_001` cycle or Ziping representation provides a stable incremental same-session direction signal across major Chinese equity indices under the frozen ridge-logistic protocol.”

That claim is not supported.

The result does **not** prove that every conceivable Chinese-calendar or Ziping representation is useless, nor does it prove that the Shanghai Composite historical result was numerically erroneous. It shows that the exact historically nominated algorithms do not survive the preregistered external-index replication standard.

## 7. Updated evidence hierarchy

1. **Shanghai Composite historical walk-forward:** `cycle` and `ziping` passed `HYBRID_ALPHA_001`.
2. **External-index historical replication:** both failed `HYBRID_REPL_001` with 0/4 complete index passes.
3. **Prospective Shanghai Composite future test:** `HYBRID_FWD_001` remains active because it was frozen before future outcomes and answers a different question: whether the Shanghai-specific historical effect persists on truly unseen future data.

Therefore the current working interpretation is:

> **Possible Shanghai-specific historical anomaly; no evidence yet of a general cross-index symbolic factor.**

## 8. Decision and stop rules

- Do **not** rescue `HYBRID_REPL_001` by dropping Shenzhen Component, CSI 300, or any other failed market.
- Do **not** reselect individual cycle/Ziping features on these replication results.
- Do **not** switch to a nonlinear model under the same hypothesis ID.
- Do **not** weaken 3/4 window stability or 3/4 index replication thresholds.
- Continue `HYBRID_FWD_001` exactly as frozen.
- Any materially different hypothesis must receive a new ID and must not be described as a confirmation of `HYBRID_ALPHA_001`.
