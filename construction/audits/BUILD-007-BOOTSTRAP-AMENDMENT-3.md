# BUILD-007-BOOTSTRAP-AMENDMENT-3 — Amended bootstrap authority (append-only)

Amends BUILD-007-BOOTSTRAP.md (as amended by AMENDMENT-1 and
AMENDMENT-2) after the aborted attempt 3
(construction/rejections/BUILD-007-attempt-3.yaml). Prior records are
immutable. Frozen BEFORE the attempt-4 candidate is finalized.

## Why amendment is required

Attempt 3 was aborted by an EXECUTOR PROCEDURAL ERROR, not a candidate
defect: the working tree had been checked out to the canonical branch
before `tools/promote.py` was invoked, so the ACCEPTED-state promoter
(v4, BUILD-006 law) executed instead of the candidate's repaired v5
promoter. The v4 promoter has no canonical-viability gate and no
staging step; it moved the canonical ref and then wrote its receipt
commit from the canonical working tree, reverting the candidate
realization in that same commit. The resulting state was rejected by its
own ledger law. Local canonical was reset to the amended parent; origin
was never advanced.

The episode is itself evidence for AUDIT-006 Obligation 4: a promotion
whose final accepted state is never verified can install a state that
fails its own law. That is the failure the repaired mechanism prevents
by staging and verifying the exact accepted state before any ref moves.

## Amended provisions

### A. parent_canonical_identity (superseding)

The commit that adds THIS amendment record — a descendant of the
attempt-3 rejection commit
ea6c7ae864b721fde377b0eaeb082f878bd02cc4. Attempt-4 candidate/BUILD-007
branches from exactly that commit.

### B. Ceremony execution locus (addition, frozen)

The gated ceremony MUST be executed with the working tree at the
CANDIDATE state, so that the code performing the ceremony is the
candidate's repaired mechanism — the same mechanism BUILD-008 will
inherit — and never the accepted-state mechanism under repair. The
executor verifies before invocation that `tools/promote.py` in the
working tree is the candidate's version. Everything else about the
ceremony, including which single object may move canonical, is
unchanged.

### C. No mechanism change authorized

No change to the privilege contract, typed probe schema, integrity
rulers, staging-ref provision, authority-transfer semantics, decision
rule, or ExceptionGrant NONE is authorized by this amendment. The
attempt-4 candidate payload is identical to attempt 3's apart from
records.

## Scope

Valid for the remainder of the BUILD-007 transition only. BUILD-008
requires no bootstrap exception.
