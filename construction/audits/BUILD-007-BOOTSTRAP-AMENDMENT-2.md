# BUILD-007-BOOTSTRAP-AMENDMENT-2 — Amended bootstrap authority (append-only)

Amends BUILD-007-BOOTSTRAP.md (as already amended by AMENDMENT-1) after
the lawful rejection of candidate attempt 2
(construction/rejections/BUILD-007-attempt-2.yaml). Prior records are
immutable. Frozen BEFORE the attempt-3 candidate is finalized.

## Why amendment is required

Attempt 2 passed PARENT_ADMITTED and SUCCESSOR_PAYLOAD_VIABLE — with the
executor's independent realm measurement agreeing on every typed probe
outcome and on the measured privilege state — and then failed at
SUCCESSOR_CANONICAL_VIABLE, which could not be evaluated AT ALL: the
staged accepted state was a dangling commit, and the independent
substrate is obtained with `git clone --no-local`, which transfers only
ref-reachable objects.

This is a genuine defect in the candidate's promoter, discovered by the
very gate AUDIT-006 Obligation 4 required, and it demonstrates the
obligation's value: under the previous architecture the transition would
have promoted and only then discovered the problem. Here the canonical
ref never moved and no authority was transferred.

A material fact about Option A follows and is frozen as part of the
architecture:

    The staged would-be accepted state must be REF-REACHABLE to be
    independently evaluable, while remaining NON-CANONICAL so that no
    authority is transferred by its existence.

## Amended provisions

### A. parent_canonical_identity (superseding)

The commit that adds THIS amendment record — a descendant of the
attempt-2 rejection commit
0983c7984f62c79d77f97fff5243ed4de30ba3f7. Attempt-3 candidate/BUILD-007
branches from exactly that commit.

### B. Staging ref (addition to the frozen FINAL_STATE_STAGED step)

The staged state S is published to a NON-CANONICAL staging branch
`staged/<transition>` in the parent repository before canonical
viability is evaluated, and that branch is deleted after the evaluation
concludes (whatever its verdict). Constraints, all frozen:

  * the staging branch is never the canonical branch and never confers
    authority; its existence is not an authority transfer;
  * it exists only across the canonical-viability evaluation window, so
    `parent_refs_digest` before/after that window are both measured with
    the staging ref present and remain equal;
  * the authority-transfer event remains exactly the expected-old-value
    update-ref of the CANONICAL branch to S, unchanged;
  * on any failure the staging branch is deleted and canonical is
    untouched.

### C. Required correction for attempt 3 (promoter only)

`tools/promote.py` must create and delete the staging branch around the
canonical-viability evaluation as specified in B. No change to the
privilege contract, typed probe schema, integrity rulers,
authority-transfer semantics, decision rule, or ExceptionGrant NONE is
authorized.

## Attempt-2 evidence (retained append-only, on the evidence branch)

    parent GateResult:            94b26a97b8758481a32e137d8b3b2f74b5652733  (PASS)
    payload viability:            29c622d32eba567ed71688cb28ec063cda4c86a8  (PASS)
    canonical viability attempt:  48f9da75fcd220a8f44899dacff5718df736ceca  (UNEVALUABLE)

## Scope

Valid for the remainder of the BUILD-007 transition only. BUILD-008
requires no bootstrap exception.
