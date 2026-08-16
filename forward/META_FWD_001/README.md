# META_FWD_001 — prospective audit map

Status: **ACTIVE / FUTURE-ONLY**  
Forward start: **2026-08-17**  
Market: Shanghai Composite (`000001`, Sina via pinned AKShare path)  
Prediction anchor: **09:25 Asia/Shanghai**

This directory contains the primary prospective symbolic-branch tournament. The
purpose of the controls below is to make later success and failure difficult to
reinterpret after outcomes are known.

## Frozen candidate family

- `cycle`
- `ziping`
- `qimen`
- `meihua` (`MEIHUA_TIME_V1`)
- negative control: `liuyao_hash` (`LIUYAO_HASH_V1`, not eligible to win)

No candidate may be added under this family ID after the first eligible record.

## Four integrity layers

### 1. Predictor-source freeze

The predictive dependency closure is compared byte-for-byte against registration
commit:

`12ddbcc66b0f1b3679c3f87ab1598cd538fdaa47`

The verifier is `metaalpha.forward_runtime_lock`. Audit/reporting/settlement code
added after registration is outside the predictor closure; predictive engines,
feature builders, model code and market preprocessing are not.

### 2. Runtime freeze

The first eligible run used CPython **3.11.15**. The exact package environment is
recorded in:

`requirements/meta-fwd-001.lock.txt`

The lockfile itself is bound to SHA-256:

`f12b6780df99f96a7904d435c42344f5b809852dbff043d568306e7721ee2a8b`

Future prediction jobs fail before producing a record if source, Python patch
version, lockfile hash, or locked runtime package versions drift.

### 3. Immutable prediction ledger

Directory:

`forward/META_FWD_001/predictions/`

Rules:

- one file per target date;
- no overwrite;
- structural eligibility is independently recomputed rather than trusting JSON flags;
- target-date training cutoff must be strictly earlier than the target date;
- exact-path Git history must show one commit touch;
- that commit must precede the target-session 09:25 anchor;
- frozen candidate/model/feature sets must match exactly.

The first record, `2026-08-17.json`, was generated before the anchor and is the
first eligible observation.

### 4. Immutable realized-outcome ledger

Directory:

`forward/META_FWD_001/realized/`

A target session may first be settled only after **15:30 Asia/Shanghai**. The
first accepted outcome snapshot locks:

- previous trading date;
- previous close;
- target close;
- close-to-close realized return;
- realized direction;
- provider/symbol;
- scoring-data manifest;
- SHA-256 binding to the corresponding immutable prediction file.

An existing realized JSON is never rewritten. If the upstream vendor later
revises an old price, that revision cannot silently change the locked first-500
confirmatory sample. A separate correction study would require an explicit new
dataset/version.

## Daily lifecycle

1. **08:10** — scheduled job starts.
2. Verify frozen Python/runtime and frozen predictor source.
3. If today's prediction already exists, refuse overwrite.
4. Otherwise build the signal using only market history through `t-1` and commit it.
5. **09:25** — eligibility anchor. A record created at/after this time is not confirmatory.
6. Market session occurs.
7. **15:30** — earliest permitted same-day outcome settlement.
8. **16:40** — scheduled settlement job audits prediction history, creates any missing immutable realized outcome, recomputes status only from locked outcomes, audits the new outcome, then commits it.
9. CI re-audits source/runtime, prediction Git history, realized Git history, and tests on every push.

## Confirmatory gate

Exactly the first **500 eligible settled market sessions** form the one-time gate
sample. Candidate requirements remain those preregistered in
`registry/meta_forward_hypotheses.yaml`, including temporal consistency, effect
size, block bootstrap and Holm correction across the four candidate branches.

A daily probability leader is descriptive only. No candidate is a winner before
the locked gate.

## Evidence hierarchy

`META_FWD_001` is the current primary prospective family. `HYBRID_FWD_001` is an
overlapping shadow check, not an independent replication. `ZIPING_FWD_001` is a
specific-rule follow-up and cannot override the primary family conclusion.

See:

- `registry/prospective_evidence_hierarchy.yaml`
- `registry/meta_fwd_001_reproducibility.yaml`

The existing `HYBRID_REPL_001` cross-index failure remains permanent negative
evidence even if a Shanghai-only prospective model later succeeds.

## Security scope

These controls provide strong reproducibility and auditability against accidental
drift and ordinary post-hoc editing. Git commits in this repository are currently
unsigned, so Git timestamps are treated as audit evidence, not as an external
trusted timestamp authority or protection against a malicious repository owner.
