# AUDIT-004 — External audit of BUILD-004 realization (received 2026-08-14)

**Verdict on BUILD-004: REALIZED_WITH_GOVERNANCE_GAPS**

BUILD-004 materially improved the construction authority: AUDIT-003
archived append-only; rule-v2 identities mechanically derived; attempt 1
genuinely rejected and preserved; attempt 2 promoted with a receipt
binding the exact realized candidate; ledger verifies at 0 violations;
GitHub Actions independently reproduced the recorded parent-law
evaluation. The generational authority mechanism is nonetheless not
closed. BUILD-005 is the Phase -1 repair; Phase 0 moves to BUILD-006.

## Central discoveries

    Authority != ExceptionAuthority
    AcceptedCodeAuthority != CandidateCodeCapability

Frozen principles:

    DecisionRule_t ∈ A_t          DecisionRule_t ∉ CallerInput
    UnacceptedCode may be evaluated, but evaluation does not imply
    ambient causal authority.

## Findings

1. **Caller-controlled expected-violation set changes the meaning of
   PASS.** P_B accepts `--expect-violation` and forwards it into G_B's
   verdict rule. Legitimate only for the externally pre-frozen
   BUILD-004 bootstrap; as a generic interface it permits
   Caller -> ExpectedViolationSet -> GateDecisionRule -> PASS ->
   Promotion — a caller could turn a failing candidate into a PASS by
   supplying its failures as the expected set.
2. **Unaccepted successor code executes with ambient host authority.**
   The prospective V_{t+1}(C) run executes candidate-controlled Python
   before final authorization, in a detached worktree.
   DetachedWorktree != Sandbox: repository refs, filesystem, process
   environment, credentials, network, and host tools remain reachable.
3. **Successor-law viability is measured but not required.** Promotion
   depends only on the parent result; V_t PASS with V_{t+1} FAIL would
   still promote, creating an authority that cannot validate the state
   in which it becomes authoritative.
4. **Pre-promotion chronology is not remotely established.** BUILD-004
   proves OutcomeReproducedAfterPromotion, not
   PrePromotionChronologyCertified. Post-promotion mirror plus
   reproduction shows compatibility with recorded history, not the
   ordering Finalize ≺ Evaluate ≺ Authorize ≺ Promote. The status name
   EVIDENCE_BOUND overclaims and must be retyped (MIRROR_BOUND /
   OUTCOME_REPRODUCED / CHRONOLOGY_UNATTESTED or equivalent).
5. **"Canonical unchanged on rejection" is semantically inaccurate.**
   Rejection appends a record, so the canonical commit advances. True
   semantics: PayloadState_{t+1} = PayloadState_t while
   GovernanceLedger_{t+1} = GovernanceLedger_t ⊕ RejectionEvent —
   the existing Genesis principle state != ledger, now to be
   mechanically represented.

## Hard obligations for BUILD-005

1. Remove caller authority over the acceptance rule. Default
   ExpectedViolations = ∅; exceptional admission only via a
   first-class ExceptionGrant ∈ AuthorityState (never CallerArguments);
   EffectiveDecisionRule_t = BaseDecisionRule_t ⊕
   AuthorizedExceptionGrant_t.
2. Prospective successor-law evaluation under a bounded capability
   surface (no canonical/governance writes, no ref updates, no
   credentials, no network) — mechanically enforced and measured, or
   the limitation reported rather than a sandbox claimed.
3. Promote(C) => V_t(C) = PASS AND V_{t+1}(C) = PASS. Parent admission
   and successor viability are distinct, both necessary; parent FAIL
   prevents candidate-code execution entirely.
4. Establish durable remote pre-promotion evidence (Option A) or
   explicitly downgrade the chronology claim (Option B).
5. Distinguish PayloadState from GovernanceLedger in ontology, law,
   and language.

## Inspection measurements (builder, 2026-08-14, pre-freeze)

- Accepted state e1b469d…: ledger verifies, 0 violations.
- `unshare -n` available and effective: network probe inside the
  namespace fails (URLError) — OS-enforced network denial usable.
- `env -i` effective: environment reducible to PATH only.
- Evidence BRANCH push succeeded where the non-branch ref push had
  failed: refs/heads/claude/genesis-evidence now exists remotely at
  the BUILD-004 GateResult chain head (c0fe623f…). Option A is
  therefore viable for BUILD-005 onward. BUILD-004's own chronology
  remains UNATTESTED: its evidence reached the remote only after its
  promotion.
- Branch protection: not enabled (owner action still pending);
  promotion exclusivity remains detection, not prevention.

## Disposition

    BUILD-004 — REALIZED_WITH_GOVERNANCE_GAPS (historical records
                immutable, including attempt 1, amendment, mirror,
                receipt)
    BUILD-005 — Phase -1 AUDIT-004 repair
    BUILD-006 — Phase 0 Genesis/contracts, only after BUILD-005 passes
                external audit
