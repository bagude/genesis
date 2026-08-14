# AUDIT-002 — External audit of BUILD-002 (received 2026-08-14)

Trust-boundary findings. These supersede the builder's stated successor
("BUILD-003 = Phase 0"); BUILD-003 is the AUDIT-002 governance repair
and Phase 0 moves to BUILD-004.

Diagnostic note recorded by the steward: the builder's post-BUILD-002
report advanced to Phase 0 without having ingested this audit —
a live demonstration that grounding requires explicit acknowledgment
and ingestion into B_t before any further transition.

## Blocking obligations

1. **Parent-law authorization.** A candidate that contains V_{t+1} may
   not use V_{t+1} as the authority that admits itself.

       Accept(C_{t+1}) => V_t(C_{t+1}) = PASS

   V_{t+1}(C_{t+1}) may be evaluated prospectively, but V_t is the
   authoritative parent law for the transition.

2. **Candidate/canonical separation with pre-promotion Gate.**

       Canonical_t -> Candidate_{t+1} -> Verify under V_t -> Gate
       -> Promote OR Reject

       Verify(Candidate) = FAIL => Canonical_{t+1} = Canonical_t

   CI after canonical mutation is attestation, not authorization.

3. **Closure-bound ExperimentEvidence.** Historical experiment evidence
   must be bound to: target identity, probe identity / definition
   identity, environment identity, result, transition / closure
   identity. A future rerun under current HEAD / current registry /
   current environment must not silently redefine the original
   historical evidence.

## Secondary findings

- rename/narrow `experiment_tree_isolation` if its measured invariant
  is only authoritative-tree status preservation
- introduce first-class environment identity
- preserve rejected candidate attempts as distinct events where
  practical

## Causal-role separation to preserve

    R_B = measurement
    E_B = experiment
    V_B = verification
    G_B = authorization
    P_B = promotion

Do not collapse them into a larger verifier.

## Disposition

Incorporated as BUILD-003 (trust-boundary closure: parent-law gate,
candidate/canonical separation, closure-bound experiment evidence).
Phase 0 (Genesis / contracts) moves to BUILD-004.
