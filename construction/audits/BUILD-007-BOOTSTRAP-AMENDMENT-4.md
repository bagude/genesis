# BUILD-007-BOOTSTRAP-AMENDMENT-4 — Amended bootstrap authority (append-only)

Amends BUILD-007-BOOTSTRAP.md (as amended by AMENDMENTS 1-3) after the
lawful rejection of attempt 4
(construction/rejections/BUILD-007-attempt-4.yaml). Prior records are
immutable. Frozen BEFORE the attempt-5 candidate is finalized.

## Why amendment is required

Attempt 4 executed the repaired mechanism correctly and was rejected at
SUCCESSOR_CANONICAL_VIABLE — the gate AUDIT-006 Obligation 4 required —
before any ref moved. It exposed a genuine FIXED-POINT DEFECT in the
candidate's own successor law:

  * `check_receipt_v5` required the receipt to name the
    canonical-viability evidence object. But the receipt lives INSIDE
    the staged accepted state, while the canonical-viability evidence is
    DERIVED FROM that state. A commit cannot name evidence about
    itself, so no staged state could ever satisfy the requirement.
  * `check_receipt_v3` additionally asserted the pre-split field name
    `successor_viability_verdict`, which schema-v5 receipts replace with
    the distinct `successor_payload_viability_verdict`.

No authority was transferred; the canonical ref never moved; payload
unchanged.

## Frozen resolution of the fixed point

Canonical viability CANNOT be a field inside the state it judges. It is
therefore an EXTERNAL, DERIVED property:

  * the schema-v5 receipt records the payload-viability evidence object
    and declares `canonical_viability: EXTERNAL_EVIDENCE`; it never
    names the canonical-viability object;
  * the CanonicalViability evidence object records
    `staged_state_commit`, which must equal the commit that adds the
    receipt — i.e. the exact accepted state;
  * `V_B` DERIVES `canonical_viability_<id>` by searching the evidence
    chain for that object: `CERTIFIED` when a PASS object names the
    accepted state, `UNCERTIFIED` otherwise. This derivation NEVER fails
    the ledger, because a bare clone legitimately has no evidence ref —
    the same honesty rule already applied to chronology.
  * the BINDING guarantee remains with the promoter: it refuses to
    publish unless canonical viability PASSED, and the evidence object
    is the durable, independently inspectable record of that gate.

Claim discipline: the ledger asserts `canonical_viability = CERTIFIED`
only where the evidence is actually present; it never asserts the
stronger property from the receipt's say-so.

## Amended provisions

### A. parent_canonical_identity (superseding)

The commit that adds THIS amendment record — a descendant of the
attempt-4 rejection commit 678c5326e5cb54b5c72e6cbef25ec86b23bd9d78.
Attempt-5 candidate/BUILD-007 branches from exactly that commit.

### B. Authorized corrections (successor law only)

  1. `check_receipt_v5`: derive canonical viability from the evidence
     chain as specified above; do not require it as a receipt field.
  2. `check_receipt_v3`: gate its pre-split field assertions to
     schema_version < 5.
  3. `promote.py`: record `canonical_viability: EXTERNAL_EVIDENCE` in
     the receipt and continue to refuse publication unless the
     canonical-viability gate returned PASS.

No change to the privilege contract, typed probe schema, integrity
rulers, staging-ref provision, authority-transfer semantics, decision
rule, or ExceptionGrant NONE is authorized.

## Attempt-4 evidence (retained append-only)

    parent GateResult:      2618503979a667ef01a93a961b715c4ae0d51667  (PASS)
    payload viability:      a2c04c6cbd0dfb0d4ebb7a805296df4e39702d93  (PASS)
    canonical viability:    10af030b9e14ce0138138d89bfff5723fa39553f  (FAIL)
    staged state evaluated: 30e377bdb05562c1d748813526fb2a937bca92f4

## Scope

Valid for the remainder of the BUILD-007 transition only. BUILD-008
requires no bootstrap exception.
