# BUILD-005-BOOTSTRAP — Frozen bootstrap authority for BUILD-005

One-transition bootstrap binding. BUILD-005 repairs the mechanism that
would otherwise admit BUILD-005, so its admission semantics are frozen
here BEFORE its candidate exists: Identity(A_005_bootstrap) ≺
Finalize(C_005). Rules and verified git identities only; all derived
values are computed mechanically at ceremony time.

## parent_canonical_identity

The commit that adds construction/proposals/BUILD-005.yaml — a
descendant of AUDIT-004's archive commit
9622a8c2aef4b06a91ce560325e201799adbcb5b and of this record's commit.
Candidate/BUILD-005 branches from exactly that commit. Full SHA
reported at freeze completion; derivable forever as the proposal
file's adding commit.

## parent authority (accepted BUILD-004 state, verified at inspection)

Manifest tools/authority.yaml (rule v2) with members:

    tools/verify_construction.py                      0ea005fad49f746216d00aea21cc25053aa00704
    tools/gate.py                                     7ae5c10dfa06b8c6f6f1822eb69e96c31388a170
    tools/promote.py                                  4803c84eedbea42f0c5ca5f41c236f8c868fc5f7
    tools/authority_lib.py                            16f86a87489736742c4275933fa5dafb2d3ee7e8
    tools/probes.yaml                                 01eb084c0d6b856d5b80da368abad96d2cf7e57b
    construction/schemas/build_proposal.schema.yaml   a706e30ba7dae9bd17b6114144bbe3d2a123d870
    construction/schemas/build_grounding.schema.yaml  dcadfd1efa6a3981883b570a876c58662ef74ddc

Authority identity is derived at ceremony time by rule v2 over the
parent canonical; never typed here.

## parent decision rule (frozen; the caller chooses nothing)

    parent_law_verdict = PASS iff the V_BUILD-004 bundle run over the
    finalized candidate yields exit 0 and ZERO violations.

    expected_violations = ∅.

No caller-supplied expected/accepted/ignored failures, waivers, or
alternate verdict rules exist in this admission. Inspection found no
parent-law defect requiring an exception; if the ceremony run
nonetheless yields violations, the outcome is REJECTION (payload
unchanged, governance ledger appends the rejection), followed by an
append-only amendment for external review — never an ad-hoc widening.

## exception policy

ExceptionGrant for BUILD-005: NONE. From BUILD-005's realized law
onward, exceptional admission exists only as a first-class grant record
present in the ACCEPTED parent canonical tree before candidate
finalization (construction/exceptions/<BUILD-NNN>.yaml), consumed by
G_B from parent state, never accepted as a caller argument.

## candidate evaluation order and capability boundary

1. Parent evaluation runs FIRST, executing only accepted parent-law
   code over candidate data. Parent FAIL ⇒ candidate successor code is
   never executed.
2. Successor viability (candidate's own law over the candidate) runs
   ONLY after parent PASS, inside this frozen CapabilityEnvelope:
   - isolated disposable clone: `git clone` from the local repository
     into a scratch directory at the exact candidate commit, with the
     origin remote REMOVED (no remotes, no credential helpers);
   - environment reduced via `env -i` to PATH and a scratch HOME (no
     inherited credentials, tokens, or proxy configuration);
   - network denied by OS namespace isolation (`unshare -n`), measured
     effective at inspection (in-namespace probe fails);
   - measured evidence recorded per run: remote list (must be empty),
     environment inventory, network-probe outcome (must fail), and
     pre/post comparison of the REAL repository's refs (must be
     identical).
   The envelope denies: canonical/governance writes, ref updates,
   credentials, network. It does NOT claim OS-image or side-channel
   isolation (declared limitation).

## promotion procedure

Promotion requires parent PASS AND successor viability PASS. Then:
atomic expected-old-value update-ref fast-forward of
claude/genesis-worktree-creation-4y9bcz from parent_canonical_identity
to the exact evaluated candidate SHA. Rejection at either stage leaves
the PAYLOAD state unchanged; the governance ledger may append the
RejectionEvent. Payload ≠ governance ledger, stated exactly.

## evidence and chronology claim (Option A, measured viable)

GateResult and ProspectiveEvaluation evidence objects are committed to
the local evidence ref AND pushed to the remote governance branch
refs/heads/claude/genesis-evidence BEFORE promotion (branch pushes
proven available where non-branch ref pushes are denied). Chronology
claim for BUILD-005: remote pre-promotion evidence exists and is
independently inspectable. If the pre-promotion branch push fails at
ceremony time, the claim downgrades to CHRONOLOGY_UNATTESTED
explicitly; promotion may proceed with the downgraded claim recorded.
BUILD-004's historical chronology remains UNATTESTED; its provenance
status is retyped MIRROR_BOUND / OUTCOME_REPRODUCED without touching
its closed records.

## bootstrap_issuer

The repository steward (bagude), through the external audit channel
that issued AUDIT-004; precedes and is not derived from any candidate
BUILD-005 state. The builder session (Claude, session
019M1VEWpY6pk11w6aPpxXC6) is executor only. The executor performs the
ceremony steps above manually because the accepted P_B carries the very
defects under repair; the corrected tools become authoritative for
BUILD-006 with no bootstrap exception.

## objects permitted to move canonical state

Exactly one: the executor's expected-old-value update-ref conditioned
on BOTH in-session results (parent PASS, viability PASS). Receipts,
evidence mirrors, and rejection records are governance-ledger appends
(Construction-Receipt commits, record namespaces only), never payload
mutations and never authorization inputs.

## scope

Valid for exactly one transition (BUILD-005).
