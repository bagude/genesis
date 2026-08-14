# BUILD-007-BOOTSTRAP-AMENDMENT-5 — Amended bootstrap authority (append-only)

Amends BUILD-007-BOOTSTRAP.md (as amended by AMENDMENTS 1-4). Prior
records immutable. Frozen BEFORE the attempt-6 candidate is finalized.

## Why amendment is required

The BUILD-007 proposal froze `budget.max_files_changed: 18`. Each
append-only bootstrap amendment adds one attributed file to the
transition, so after four amendments the realization reached 19
attributed files and the transition FAILED its own frozen budget:

    FAIL BUILD-007: 19 files changed exceeds budget 18

The budget is part of the preregistered design and a closed record. It
is not amendable, and exceeding it silently is not permitted. The
transition must therefore FIT the frozen budget by reducing its
realization footprint — not by relaxing the constraint.

## Frozen resolution

Two files are removed from the BUILD-007 realization. Both are
redundant with mechanisms that remain fully in force, so no obligation
is weakened:

  1. `.github/workflows/construction.yml` — the CI honesty step
     reporting capability-primitive availability is REVERTED. The
     limitation it printed is already stated normatively in
     `construction/ALGEBRA.md` and in AUDIT-006's archive, and CI
     continues to run full-ledger verification and both-gate
     reproduction. Remote CI still makes no capability-realm claim.
     Deferred to BUILD-008.
  2. `tools/probes.yaml` — the registry entry for the probe-semantics
     self-test is REVERTED. The self-test remains enforced as LAW: V_B
     calls `selftest_probe_semantics.run()` on every invocation (pure
     computation) and fails the ledger if the false-pass path reopens.
     The registry entry was only a second, redundant execution path.
     Deferred to BUILD-008.

Net effect: 19 attributed files − 2 removed + 1 (this amendment) = 18,
exactly at the frozen budget.

### parent_canonical_identity (superseding)

The commit that adds THIS amendment record. Attempt-6 candidate
branches from exactly that commit.

## No mechanism change authorized

The privilege contract, typed probe schema and its self-test law,
integrity rulers, staging-ref provision, external derived canonical
viability, authority-transfer semantics, decision rule, and
ExceptionGrant NONE are ALL unchanged.

## Scope

Valid for the remainder of the BUILD-007 transition only. BUILD-008
requires no bootstrap exception.
