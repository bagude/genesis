# BUILD-006-BOOTSTRAP — Frozen bootstrap authority for BUILD-006

One-transition bootstrap binding, frozen BEFORE the BUILD-006 candidate
exists: Identity(A_006_bootstrap) ≺ Finalize(C_006). Rules and verified
git identities only; derived values computed mechanically at ceremony
time.

## The bootstrap boundary problem (explicit)

BUILD-006 repairs the prospective isolation mechanism. Therefore
BUILD-006's OWN successor-viability evaluation must NOT derive its
isolation from the candidate's new, not-yet-accepted tools/prospective.py
— that would let the object under repair justify itself. This record
freezes the isolation PROCEDURE itself (below), proven during
inspection, and the executor provides isolation from this frozen
procedure. The candidate's tools/prospective.py is validated as data
(its viability verdict is measured) but is NOT trusted to bound its own
execution during BUILD-006's admission. From BUILD-007 onward the
accepted BUILD-006 tools/prospective.py provides isolation mechanically,
with no bootstrap exception.

## parent_canonical_identity

The commit that adds construction/proposals/BUILD-006.yaml — a
descendant of AUDIT-005's archive commit
e4815e4eba27e4953ee5c197144bb27d5f8c1ff2 and of this record's commit.
Candidate/BUILD-006 branches from exactly that commit. Full SHA
reported at freeze completion; derivable as the proposal file's adding
commit.

## parent authority (accepted BUILD-005 state, verified at inspection)

Manifest tools/authority.yaml (rule v2) members:

    tools/prospective.py                              59cb24ffb764380da5dd430bc2b2fe26e2012442
    tools/verify_construction.py                      8cd98124de2fb00a428e5f13edbbe2d8af67f0f3
    tools/gate.py                                     dddce3bb635dce1f02af9ce6ae51b2d777ac83ef
    tools/promote.py                                  df4f32ca0b6d85e2b264b1b41776ff04c631605f
    tools/authority_lib.py                            16f86a87489736742c4275933fa5dafb2d3ee7e8
    tools/probes.yaml                                 01eb084c0d6b856d5b80da368abad96d2cf7e57b
    construction/schemas/build_proposal.schema.yaml   a706e30ba7dae9bd17b6114144bbe3d2a123d870
    construction/schemas/build_grounding.schema.yaml  dcadfd1efa6a3981883b570a876c58662ef74ddc

Authority identity derived at ceremony by rule v2 over the parent
canonical; never typed here.

## decision rule (frozen; caller chooses nothing)

    parent_law_verdict = PASS iff the V_BUILD-005 bundle run over the
    finalized candidate yields exit 0 and ZERO violations.
    expected_violations = ∅.  ExceptionGrant = NONE.

No grant record for BUILD-006 exists in the parent tree; the ceremony
verifies its absence. Parent evaluation executes ONLY accepted-law code
over candidate data and runs first; parent FAIL ⇒ candidate code is
never executed; payload unchanged; ledger may append the rejection.

## FROZEN isolation realm procedure (the bootstrap boundary)

Successor viability for BUILD-006 is evaluated by executing the
candidate's own tools/verify_construction.py over an independent copy of
the candidate, inside a realm the EXECUTOR constructs by these exact,
frozen steps (proven feasible at inspection; not delegated to candidate
code):

1. Independent substrate: `git clone --no-local --no-hardlinks
   <parent_repo> <scratch>/repo`; `git -C <scratch>/repo checkout
   <candidate_sha>`; `git -C <scratch>/repo remote remove origin`.
   Independence is ADVERSARIALLY tested: 0 hard-linked objects between
   clone and parent object stores.
2. Realm root <scratch>/realm with read-only bind mounts of /usr, /bin,
   /lib, /lib64, /etc, a mounted /proc, and a single writable /work
   (the repo copy) plus writable /tmp, both chown 65534:65534.
3. Execution: `unshare -m -n` (mount + network namespaces); apply the
   binds; `chroot <realm>`; `setpriv --reuid=65534 --regid=65534
   --clear-groups`; run python3 over the candidate verifier with
   HOME=/work.

## FROZEN capability contract (measured, not asserted)

Inside the realm the following must hold, each proven by an adversarial
probe run in the same realm as the viability evaluation:

    see_parent_repo         = DENIED   (path absent in realm)
    write_parent_repo       = DENIED
    write_parent_refs       = DENIED
    write_parent_git_objects= DENIED
    write_usr / write_etc   = DENIED   (read-only binds)
    write_host_root         = DENIED   (unprivileged uid)
    forbidden_env           = DENIED   (env reduced to PATH+HOME)
    network                 = DENIED   (unshare -n)
    write_scratch           = ALLOWED  (the only writable location)

and, measured on the host AFTER the realm exits:

    parent_repo_refs_unchanged        = true
    parent_repo_worktree_unchanged    = true (sentinel digest equal)
    parent_git_object_count_unchanged = true

successor_viability_verdict = PASS iff the candidate verifier exits 0
with zero violations inside the realm AND every DENIED probe above is
DENIED AND every host-after invariant holds.

## promotion / rejection

Promotion requires parent PASS AND successor viability PASS. Atomic
expected-old-value update-ref fast-forward from parent_canonical to the
exact candidate SHA. Rejection at either gate leaves PayloadState
unchanged; GovernanceLedger may append the RejectionEvent. Exactly one
object moves canonical: the executor's expected-old-value update-ref
conditioned on both PASS results.

## evidence and chronology (honest)

GateResult, ProspectiveEvaluation (with capability_envelope and
adversarial_probes), and receipt are committed to the local evidence
ref and pushed to the remote governance branch claude/genesis-evidence.
Chronology claim frozen at REMOTE_EVIDENCE_PRESENT only;
PRE_PROMOTION_CHRONOLOGY = UNATTESTED (no externally-ordered platform
event proves push-before-promotion; graph membership proves presence
only). The certified capability envelope is read by V_B from the bound
ProspectiveEvaluation evidence object, never from a receipt assertion.

## bootstrap_issuer

The repository steward (bagude), through the external audit channel that
issued AUDIT-005; precedes and is not derived from any candidate
BUILD-006 state. The builder session (Claude, session
019M1VEWpY6pk11w6aPpxXC6) is executor only, performing the frozen
procedure because the accepted prospective evaluator is the object under
repair.

## scope

Valid for exactly one transition (BUILD-006). BUILD-007 requires no
bootstrap exception: it is admitted by the accepted BUILD-006 tools.
