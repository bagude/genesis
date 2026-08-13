# AUDIT-001 — External audit of BUILD-001 (received 2026-08-13)

**Verdict: REALIZED / AUDIT-000 MOSTLY CLOSED / NEW GOVERNANCE DIFFERENTIAL**

Independent GitHub Actions reproduction is now observed and PASS.
Proposal precedence, scope, budget, lifecycle, probe execution, and
format-2 measurement matching are materially implemented rather than
narrated.

## Findings

| # | Result  | Finding                                                          |
|---|---------|------------------------------------------------------------------|
| 1 | FAIL    | R_B executes proposal-controlled arbitrary shell commands; measurement is not causally read-only |
| 2 | FAIL    | closed transitions remain attribution-extensible: future commits can reuse an already-grounded Construction-Transition ID and change historical derived measurements |
| 3 | FAIL    | closed proposal/audit records are not explicitly immutable; proposal commits are namespace-restricted but not current-record-restricted |
| 4 | PARTIAL | EvidenceProvenance verifies a permissive SHA-prefix relation rather than full/unambiguous object identity |
| 5 | PASS    | independent CI reproduction now observed on ea521ee               |

## Constraint imposed on the successor proposal

Distinguish passive measurement from active experiment and establish
closure:

    K_{R_B}^write                = ∅
    Grounded(P_i)               => Attribution(P_i) frozen
    ClosedRecords_i              immutable
    EvidenceRef_i                = CanonicalCommitIdentity_i

Not implementation instructions. The successor must preregister the
mechanism chosen to satisfy or reject each obligation before
realization.

## Theoretical result recorded by the auditor

BUILD-000 taught: ClaimedMeasurement ≠ Measurement.
AUDIT-001 extends it: a measuring instrument that executes
proposal-controlled commands is itself an actuator — Measurement and
Experiment are distinct operators with distinct capability sets.

## Disposition

Incorporated as BUILD-002 (governance closure: measurement/experiment
separation, attribution freeze, record immutability, canonical evidence
identity). Phase 0 (Genesis / contracts) moves to BUILD-003.
