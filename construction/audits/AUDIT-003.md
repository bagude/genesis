# AUDIT-003 — External audit of BUILD-003 realization (received 2026-08-14)

**Verdict on BUILD-003: REALIZED_WITH_GOVERNANCE_DEFECT**

BUILD-003's governance architecture is directionally correct. Two
blocking defects were found in the realized causal authority chain.
Historical records are immutable; correction is append-only via
BUILD-004. Phase 0 moves to BUILD-005.

## Core discovery

    EvidenceContent != EvidenceProvenance

A record saying `parent_law_verdict: PASS` does not prove that
V_t(candidate) actually returned PASS. A field saying `issuer: A_t`
does not prove A_t causally produced the record. The required topology
is not `YAML("PASS") -> P_B -> canonical` but
`V_t(candidate) -> G_B -> authoritative outcome -> authorization ->
P_B -> canonical`.

Frozen principles:

    External storage != external authority.
    Claimed issuer != proven issuer.
    A claim about a causal event is not evidence of that event merely
    because its fields are internally consistent.

## Finding 1 — Bootstrap authority identity is incorrect

PRE-AUDIT-003-BOOTSTRAP froze four parent-law member blobs (all
individually correct and independently verified) and recorded:

    a498931e482a1022e03f80f3291d75f28177363e5f65ee05d42a1a10a69ad4ac

Mechanical application of the declared rule — SHA256 over sorted
"<blob> <path>" lines, newline-joined, trailing newline — yields:

    38cbeab3809aa56a2a697e89677594087f1117063fba46832119418021ab882b

Builder inspection (2026-08-14) confirmed the discrepancy and its
cause: the frozen value was computed over a hand-composed,
path-grouped line ordering instead of the declared sorted-line
ordering.

    historical_recorded_identity:
        a498931e482a1022e03f80f3291d75f28177363e5f65ee05d42a1a10a69ad4ac
    mechanically_derived_identity (rule as declared/implemented):
        38cbeab3809aa56a2a697e89677594087f1117063fba46832119418021ab882b
    discrepancy: recorded != derived; member blobs correct
    epistemic_status: RECORDED_IDENTITY_INVALID / MEMBERS_VERIFIED

This value also propagated into the BUILD-003 GateReceipt and the
BUILD-003 grounding evidence field. Those records remain immutable;
this archive is the correction. The BUILD-003 discrepancy must remain
explicitly visible in successor law and never be silently normalized.

Required invariant from BUILD-004 onward: authority identities are
never manually recorded digests; they are mechanically derived from
actual git objects (parent canonical, manifest, verified member blobs)
by versioned, deterministic, unambiguous canonicalization, checked
before authorization/promotion.

## Finding 2 — GateReceipt authenticity is not established

The BUILD-003 promoter design consumes an external YAML receipt and
checks its contents (verdict, authority identity, target, fast-forward)
but the receipt is not authenticated as an output of G_B. An actor able
to invoke P_B could construct a syntactically valid receipt claiming
PASS without causally running G_B.

    ExternalToCandidate(receipt): achieved.
    ProducedByGate(receipt): NOT mechanically established.

BUILD-003's GateReceipt authenticity is not mechanically
reconstructable from current ledger evidence. BUILD-003 authorization
is therefore NOT claimed as fully certified.

## Hard obligations for BUILD-004

1. Promote(C) => V_t(C) ACTUALLY executed and returned PASS. No path:
   fabricated PASS data -> P_B -> canonical.
2. Receipt is evidence, not authority-by-assertion. Distinguish
   GateResult / AuthorizationDecision / PromotionReceipt /
   PostPromotionAttestation.
3. V_B verifies provenance, not only receipt content:
   ValidReceipt(r) => r causally bound to an authorized evaluation of
   exactly r.target_commit under exactly r.parent_authority.
4. Authorization binds parent canonical, parent authority, exact
   candidate, environment, and actual evaluation evidence. A PASS under
   A_t must not silently authorize under A_{t+1}.
5. Pre-promotion chronology Finalize ≺ Evaluate ≺ Authorize ≺ Promote
   must be reconstructable from durable evidence, without trusting the
   builder's prose.

## Standing limitations

Promotion exclusivity remains law-with-detection, not prevention: the
branch is unprotected, so unauthorized writes are detectable but not
physically impossible. This does not excuse receipt forgery within the
lawful P_B path.

## Disposition

    BUILD-003 — realized; AUDIT-003 governance defects discovered
                (REALIZED_WITH_GOVERNANCE_DEFECT)
    BUILD-004 — Phase -1 AUDIT-003 repair
    BUILD-005 — Phase 0 Genesis/contracts, only after BUILD-004 passes
                external audit
