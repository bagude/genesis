# BUILD-006-BOOTSTRAP-AMENDMENT-1 — Amended bootstrap authority (append-only)

Amends construction/audits/BUILD-006-BOOTSTRAP.md after the lawful
rejection of candidate attempt 1
(construction/rejections/BUILD-006-attempt-1.yaml). The original record
is immutable. Frozen BEFORE the attempt-2 candidate is finalized,
preserving Identity(A_006_bootstrap) ≺ Finalize(C_006').

## Why amendment is required

Attempt 1 passed BOTH gates and its isolation contract was fully
certified (all forbidden effects DENIED, 0 shared objects, host-after
invariants intact). The candidate was nonetheless rejected at
post-promotion ledger verification by its OWN law: the candidate
verifier's check_receipt_v3 applied BUILD-005-era envelope keys
(network_denied, real_repo_refs_unchanged) to the schema-v4 capability
envelope, which uses probe_* and parent_*_unchanged keys. The defect is
successor-law self-consistency only and is invisible until a BUILD-006
receipt exists. The local promotion was rolled back (payload returned
to parent 416ea1e); the rejection is a governance-ledger append.

Only ONE thing changes: parent_canonical advances past the rejection
commit. The frozen realm PROCEDURE, capability CONTRACT, decision rule
(zero violations, ExceptionGrant NONE), and evaluation/promotion
mechanism are UNCHANGED.

## Amended provision

### parent_canonical_identity (superseding)

The commit that adds THIS amendment record — a descendant of the
attempt-1 rejection commit c5981d3e853034f16047e40d3c08dd9b1657a6c8.
Attempt-2 candidate/BUILD-006 branches from exactly that commit. Full
SHA reported at freeze completion; derivable as this file's adding
commit.

### Required fix for attempt 2 (successor law only)

check_receipt_v3's envelope-key assertions must be gated to
schema_version == 3; schema-v4 receipts are certified solely by
check_receipt_v4 reading the capability envelope from the bound
prospective evidence. The attempt-2 candidate's own prospective run
must yield ZERO violations WITH a v4 receipt present (the condition
attempt 1 failed), so the successor viability run inside the realm must
be performed against a candidate that already contains its own receipt
shape — verified by the executor re-running full ledger verification on
the promoted state before finalizing the receipt as evidence.

## Attempt-1 evidence (durable on remote evidence branch)

    gate_evidence_object:      99e7e80f38dd4f542e59b4345ffc6a91ff7224f8
    viability_evidence_object: 0c19807e6b316eb50663a52aeec4d8d40fa26fd1
    both PASS; isolation certified; rejection was successor-law
    self-consistency only.

## Scope

Valid for the remainder of the BUILD-006 transition only. Everything
else in BUILD-006-BOOTSTRAP.md remains in force. BUILD-007 requires no
bootstrap exception.
