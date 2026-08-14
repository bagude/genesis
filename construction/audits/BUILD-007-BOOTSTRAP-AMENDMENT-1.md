# BUILD-007-BOOTSTRAP-AMENDMENT-1 — Amended bootstrap authority (append-only)

Amends construction/audits/BUILD-007-BOOTSTRAP.md after the lawful
rejection of candidate attempt 1
(construction/rejections/BUILD-007-attempt-1.yaml). The original record
is immutable. Frozen BEFORE the attempt-2 candidate is finalized,
preserving Identity(A_007_bootstrap) ≺ Finalize(C_007').

## Why amendment is required

Attempt 1 was rejected at PARENT_ADMITTED — the first gate — because the
candidate's grounding asserted `typed_probe_semantics_selftest` in
`observed`, a key introduced by the candidate's own successor law and
therefore outside the parent law's derived vocabulary. BUILD-004's
law-evolution rule requires novel measurements to enter a candidate's
grounding as `reported_` keys and to become derived vocabulary only for
SUBSEQUENT transitions. The parent law refused correctly.

Two properties held exactly as the frozen procedure requires and are
recorded here as evidence of the ordering, not as claims:

  * candidate code was NEVER executed — parent admission failed before
    any prospective evaluation (success condition 10);
  * the executor's INDEPENDENT realm measurement, performed before
    admission, certified privilege (NoNewPrivs=1; CapInh, CapPrm,
    CapEff, CapBnd, CapAmb all zero; uid/gid 65534) and all forbidden
    effects DENIED with the scratch control ALLOWED.

Failed-attempt GateResult evidence object:
567ee1d5c9e4e6bae571e6a1820db2cdacc9ccff (retained append-only).

Only ONE provision changes: parent_canonical advances past the rejection
commit. The frozen privilege contract, typed probe schema, integrity
rulers, Option A staging architecture, authority-transfer state machine,
decision rule (zero expected violations), and ExceptionGrant NONE are
ALL UNCHANGED.

## Amended provision

### parent_canonical_identity (superseding)

The commit that adds THIS amendment record — a descendant of the
attempt-1 rejection commit
618c9c84539a17e059cbbec534e3f1d8c4f42602. Attempt-2
candidate/BUILD-007 branches from exactly that commit. Full SHA reported
at freeze completion; derivable as this file's adding commit.

### Required correction for attempt 2 (grounding record only)

`typed_probe_semantics_selftest` must be removed from the grounding's
`observed` mapping. The property it names is already carried lawfully by
the `reported_false_pass_selftest: CLOSED` key, and the measurement
itself remains enforced by V_B on every run — it simply may not be
ASSERTED as derived vocabulary in the transition that introduces it.
That key becomes legitimate derived vocabulary for BUILD-008 onward.

No change to any tool, contract, or mechanism is authorized by this
amendment.

## Scope

Valid for the remainder of the BUILD-007 transition only. Everything
else in BUILD-007-BOOTSTRAP.md remains in force. BUILD-008 requires no
bootstrap exception.
