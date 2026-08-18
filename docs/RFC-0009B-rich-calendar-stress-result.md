# RFC-0009B — Rich Gregorian calendar stress result

Date: 2026-08-18  
Experiment: `META_CALENDAR_STRESS_2025_001`  
Status: **RETROSPECTIVE DIAGNOSTIC / NO PROMOTION**

## 1. The rich Gregorian baseline is not itself superior

On the 393-session 2025-01-02..2026-08-17 test:

- frozen market baseline LogLoss: `0.692936`
- rich Gregorian baseline LogLoss: `0.693622`

The added day-of-month, ISO-week, quarter, month-end distance and annual Fourier terms therefore worsen the ordinary market model in aggregate. `rich_calendar` must not replace the frozen ordinary baseline merely because symbolic blocks beat it.

## 2. Absolute stress-test result versus the original market baseline

| Model | LogLoss | Improvement vs original market baseline |
|---|---:|---:|
| rich calendar + hash control | 0.691294 | +0.001642 |
| rich calendar + Ziping | 0.692419 | +0.000517 |
| original market baseline | 0.692936 | 0 |
| rich calendar + Qimen | 0.693284 | -0.000348 |
| rich calendar | 0.693622 | -0.000686 |
| rich calendar + Cycle | 0.693971 | -0.001035 |
| rich calendar + Meihua | 0.698187 | -0.005251 |

For comparison, before adding rich Gregorian controls the 2025+ improvements versus the same market baseline were approximately:

- hash: `+0.002281`
- Ziping: `+0.001168`
- Qimen: `+0.000611`
- Cycle: `+0.000603`
- Meihua: `-0.004645`

Thus richer ordinary calendar structure absorbs a material fraction of the apparent hash/Ziping effect and destroys the absolute Cycle/Qimen advantage, but it does not fully absorb hash or Ziping.

## 3. Interpretation

This result rejects two simplistic stories:

1. **“All symbolic gain is merely missing Gregorian seasonality.”** False as a complete explanation: hash and Ziping retain residual absolute improvement.
2. **“Ziping survives calendar controls, therefore Ziping is validated.”** Also false: its absolute improvement shrinks to only about `+0.000517` LogLoss and its date alignment has not yet established specificity versus dense shifted-state nulls.

The current hierarchy is therefore:

- `liuyao_hash`: strongest residual deterministic time-encoding candidate, but explicitly synthetic;
- `ziping`: weak residual traditional candidate worth specificity testing;
- `cycle`: increasingly consistent with generic calendar/time partitioning;
- `qimen`: weak/unstable;
- `meihua_time_v1`: historical failure.

## 4. Decision

Do not add more symbolic features. The immediate discriminator is `META_DENSE_SHIFT_NULL_2025_001` plus the daily-expanding reconstructions. Ziping can only move upward if the exact alignment remains unusually strong under the denser shift family and under daily refitting.

Nothing here alters `META_FWD_001`.
