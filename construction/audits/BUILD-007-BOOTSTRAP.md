# BUILD-007-BOOTSTRAP — Frozen bootstrap authority for BUILD-007

One-transition binding, frozen BEFORE the BUILD-007 candidate exists:
Identity(A_007_bootstrap) ≺ Finalize(C_007). Rules and verified git
identities only; derived values computed mechanically at ceremony time.

## Bootstrap boundary (explicit)

BUILD-007 repairs the privilege, probe, ruler, and final-state semantics
that would otherwise evaluate BUILD-007. Therefore the executor performs
the FROZEN procedures below — frozen here, proven feasible during
AUDIT-006 inspection — and the candidate's own tools are evaluated AS
DATA, never trusted to bound or certify their own admission. From
BUILD-008 the accepted BUILD-007 tools do this mechanically with no
bootstrap exception.

## parent_canonical_identity

The commit that adds construction/proposals/BUILD-007.yaml — a
descendant of AUDIT-006's archive commit
b10ca271dfec8ad3c18e00ab461f887e05fd6917 and of this record's commit.
Candidate/BUILD-007 branches from exactly that commit. Full SHA reported
at freeze completion; derivable as the proposal file's adding commit.

## parent authority (accepted BUILD-006 state, verified at inspection)

Manifest tools/authority.yaml (rule v2) members:

    tools/prospective.py                              4948b7c8bc515bd59359eb6cc3e3b917fbdf85b4
    tools/realm_probe.py                              a79b5825ab222154cb479bb32e68600c745d61f2
    tools/verify_construction.py                      d9fae90a426b04f74cef1891cc476d3f1af1cdb7
    tools/gate.py                                     dddce3bb635dce1f02af9ce6ae51b2d777ac83ef
    tools/promote.py                                  f0db87ca90916e48939b61c042b8319eccdf718e
    tools/authority_lib.py                            16f86a87489736742c4275933fa5dafb2d3ee7e8
    tools/probes.yaml                                 01eb084c0d6b856d5b80da368abad96d2cf7e57b
    construction/schemas/build_proposal.schema.yaml   a706e30ba7dae9bd17b6114144bbe3d2a123d870
    construction/schemas/build_grounding.schema.yaml  dcadfd1efa6a3981883b570a876c58662ef74ddc

Authority identity derived at ceremony by rule v2 over the parent
canonical; never typed here. Parent admission uses the accepted
BUILD-006 verifier bundle, whose AUDIT-006 limitations (weak rulers,
untyped probes) are acknowledged: parent admission judges LEDGER LAW
conformance, and the capability certification of this transition rests
on the repaired frozen procedures below, not on BUILD-006's rulers.

## decision rule (frozen; caller chooses nothing)

    parent_law_verdict = PASS iff the V_BUILD-006 bundle run over the
    finalized candidate yields exit 0 and ZERO violations.
    expected_violations = ∅.  ExceptionGrant = NONE.

Absence of construction/exceptions/BUILD-007.yaml in the parent tree is
verified at ceremony start. Parent admission executes only accepted-law
code over candidate data and runs FIRST; parent FAIL ⇒ candidate code is
never executed; payload unchanged; ledger may append the rejection.

## FROZEN privilege contract (Obligation 1)

Realm entry is `unshare -m -n` → bind mounts remounted
`ro,nosuid,nodev` for /usr,/bin,/lib,/lib64,/etc → minimal /dev nodes →
chroot → `setpriv --reuid=65534 --regid=65534 --clear-groups
--no-new-privs --bounding-set=-all --inh-caps=-all` (ambient empty).
Certified privilege state, read from /proc/self/status INSIDE the realm:

    NoNewPrivs = 1
    CapInh = CapPrm = CapEff = CapBnd = CapAmb = 0000000000000000
    uid = gid = 65534

Adversarial escalation probes (see typed schema) must each be DENIED.
Claim scope: privilege monotonicity under this lattice. NOT claimed:
kernel-exploit resistance, side-channel isolation, VM-grade isolation.

## FROZEN typed probe schema (Obligation 2)

Each probe declares probe_id, attempted_effect, expected_outcome, and
predicates yielding exactly one observed_outcome ∈ {DENIED, ALLOWED,
ERROR, INCONCLUSIVE}. verdict = PASS iff observed_outcome equals the
probe's expected_outcome. An arbitrary exception yields ERROR (verdict
FAIL), never DENIED. Visibility probes are positive tests: a visible
parent yields ALLOWED ⇒ FAIL. Certification requires every declared
probe verdict = PASS, including the positive control (scratch writable
= ALLOWED expected).

## FROZEN integrity rulers, scope and metric (Obligation 3)

    parent_tracked_worktree_digest — SCOPE: every path reported by
      `git ls-files -s` in the parent repository. METRIC: SHA-256 over
      sorted "<mode> <sha256(file bytes)> <path>" lines, computed by
      reading files only. Detects uncommitted content and mode changes.
      IGNORED (declared): untracked files, ignored paths, .git internals
      other than those below, timestamps.
    parent_object_store_digest — SCOPE: every regular file under
      .git/objects (loose objects, packs, indexes). METRIC: SHA-256 over
      sorted "<sha256(file bytes)> <relpath>" lines. Detects content
      mutation at equal object count.
    parent_refs_digest — SCOPE: all refs. METRIC: SHA-256 over
      `for-each-ref` refname/objectname lines.

Certification asserts IntegrityBefore(Scope) = IntegrityAfter(Scope) for
each named scope — never the unqualified word "unchanged".

## FROZEN final-state architecture: OPTION A (Obligation 4)

    CANDIDATE_FINALIZED
      -> PARENT_ADMITTED            (V_t(C) PASS, accepted code)
      -> SUCCESSOR_PAYLOAD_VIABLE   (V_{t+1}(C) in realm, probes+rulers)
      -> FINAL_STATE_STAGED         (commit S on top of C containing the
                                     receipt and evidence mirrors — the
                                     EXACT would-be accepted state)
      -> SUCCESSOR_CANONICAL_VIABLE (V_{t+1}(S) in realm)
      -> AUTHORIZED
      -> PUBLISHED / AUTHORITY_TRANSFERRED

Hash(Stage) = Hash(FinalAcceptedState) holds by construction: publication
fast-forwards canonical to exactly S, and NOTHING is appended to
canonical afterwards for this transition. The CanonicalViability evidence
object is external (evidence branch) and therefore does not perturb S.

**Authority transfer event** = the single atomic expected-old-value
`update-ref` of the canonical branch to S. Before it, S is provisional
and A_t remains authoritative; after it, A_{t+1} governs. No provisional
authority transfer occurs at any earlier step. Failure at ANY gate ⇒ no
ref movement ⇒ PayloadState unchanged; the GovernanceLedger may append a
RejectionEvent, and all evidence for failed attempts is retained
append-only.

## remote attestation (honest, unchanged)

The hosted runner cannot create the namespace realm. CI may establish
parent-law reproduction, successor semantic conformance, and
receipt/evidence integrity; it must NOT claim remote reproduction of the
capability realm.

## bootstrap_issuer

The repository steward (bagude), through the external audit channel that
issued AUDIT-006; precedes and is not derived from any candidate
BUILD-007 state. The builder session (Claude, session
019M1VEWpY6pk11w6aPpxXC6) is executor only.

## objects permitted to move canonical state

Exactly one: the executor's expected-old-value update-ref publishing S,
conditioned on parent admission PASS, payload viability PASS, and
canonical viability PASS. Capability-level exclusivity remains
unenforced (branches unprotected) — detection, not prevention.

## scope

Valid for exactly one transition (BUILD-007). BUILD-008 requires no
bootstrap exception.
