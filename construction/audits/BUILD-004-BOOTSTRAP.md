# BUILD-004-BOOTSTRAP — Frozen bootstrap authority for BUILD-004

One-transition bootstrap binding. The accepted BUILD-003 state contains
the very G_B/P_B mechanism AUDIT-003 found incomplete, so the defective
P_B is not assumed sufficient authority for the transition that repairs
it. Invariant: Identity(A_004_bootstrap) ≺ Finalize(C_004).

Lesson of AUDIT-003 Finding 1 applied: this record freezes RULES and
verified git object identities; it never freezes a hand-composed
digest. All identity values are derived mechanically at ceremony time
by the frozen rule and reported with their derivation transcript.

## parent_canonical_identity

The commit that adds construction/proposals/BUILD-004.yaml — the last
preregistration commit, a descendant of AUDIT-003's archive commit
0e810f6003cd699351bef26082b2c2db2b162a55 and of this record's commit.
Candidate/BUILD-004 branches from exactly that commit. Its full SHA is
fixed by git content addressing at commit time, reported in the
construction dialogue at freeze completion, and derivable forever as
the adding commit of the BUILD-004 proposal file.

## current authority manifest / member identities (accepted BUILD-003 state)

Verified at inspection against canonical a396229c…/HEAD:

    tools/authority.yaml                              ae4ce9902ed65d660c28d8d1d56b0b240498c612
    tools/verify_construction.py                      3f64881e51f056e15aad059f1020d2afc8498a96
    tools/gate.py                                     96f890aa20fb3f6d292f5cfaef6487c048b29017
    tools/promote.py                                  877e358878f788efcc347844fd44aea0766b2501
    tools/probes.yaml                                 01eb084c0d6b856d5b80da368abad96d2cf7e57b
    construction/schemas/build_proposal.schema.yaml   a706e30ba7dae9bd17b6114144bbe3d2a123d870
    construction/schemas/build_grounding.schema.yaml  dcadfd1efa6a3981883b570a876c58662ef74ddc

The evaluation bundle for BUILD-004 admission is the verifier subset:
verify_construction.py, probes.yaml, and the two schemas, at exactly
the blob identities above, extracted by blob id from the parent
canonical commit (never by path from a working tree).

## known AUDIT-003 defects (in force during this admission)

1. Recorded bootstrap authority identity for BUILD-003 is invalid
   (a498931e… vs derived 38cbeab3…) — archived in AUDIT-003; the
   BUILD-003 GateReceipt and grounding evidence carry the invalid
   value; those records stay immutable.
2. GateReceipt provenance is content-only; the V_BUILD-003 promoter
   would accept a fabricated receipt. For THIS admission no receipt is
   consumed as authority at all (see promotion mechanism below).
3. Discovered at inspection, declared here: V_BUILD-003's receipt law
   (RECEIPT_REQUIRED_FROM = 4) is gate-incompatible — a finalized,
   unpromoted BUILD-004 candidate cannot lawfully contain its own
   promotion receipt, so the parent-law run over C_004 necessarily
   reports exactly one violation:

       "BUILD-004: closed transition has no promotion receipt
        (required from BUILD-004)"

   Frozen verdict rule for this admission: parent_law_verdict = PASS
   iff the violation set of the parent-law run equals exactly that
   single violation and the run's derived measurements for BUILD-004
   otherwise conform. Any other violation => FAIL => no promotion.

## bootstrap_issuer

The repository steward (bagude), acting through the external audit
channel that issued AUDIT-003 and this bootstrap condition; precedes
and is not derived from any candidate BUILD-004 state. The builder
session (Claude, session 019M1VEWpY6pk11w6aPpxXC6) is executor only.

## evaluation mechanism (exact)

1. Candidate finalized on candidate/BUILD-004; SHA fixed before any
   authoritative evaluation.
2. Executor verifies the four evaluation-bundle blobs against the
   identities frozen above, extracts them by blob id into a detached
   worktree of the candidate commit, and executes the parent verifier
   there.
3. The complete run output, exit code, violation set, environment
   identity, target commit/tree, parent canonical identity, and the
   authority identity derived by rule v2 (below) are written as a
   content-addressed GateResult evidence object committed to the
   dedicated evidence ref refs/construction/evidence and PUSHED TO THE
   REMOTE BEFORE ANY PROMOTION, creating durable pre-promotion
   chronology evidence outside the candidate.

## authority identity rule v2 (frozen; values always derived, never typed)

    identity = SHA256 of UTF-8:
        "authority-rule:v2\n"
        "parent:<full parent canonical sha>\n"
        "manifest:<git blob sha of tools/authority.yaml at parent>\n"
        + sorted "<blob> <path>" lines of the manifest members,
          newline-joined, with trailing newline

For THIS admission, members are the seven entries frozen above (the
accepted-state manifest plus the manifest file itself is bound via the
"manifest:" line). The ceremony computes the value mechanically and
records the exact input serialization alongside the digest in the
evidence object.

## promotion mechanism (exact)

Promotion is causally coupled to the evaluation: the executor promotes
ONLY from the in-session result of step 2/3 above — no receipt or other
document is consumed as authorization input. Mechanics: atomic
expected-old-value update-ref fast-forward of
claude/genesis-worktree-creation-4y9bcz from parent_canonical_identity
to the exact evaluated candidate SHA (full-SHA equality with the
evidence object's target). FAIL => canonical unchanged; the evidence
object of the failed run is preserved on the evidence ref and the
attempt recorded under construction/rejections/.

## evidence proving the evaluation occurred

The pre-promotion GateResult evidence object on refs/construction/
evidence (content-addressed, pushed before promotion), containing the
full verifier output; plus post-promotion remote CI re-attestation.
The evaluation is independently reproducible: extract the frozen blobs
from the parent canonical and re-run against the candidate SHA;
verdict and violation set must match the evidence object.

## object permitted to move canonical state

Exactly one: the executor's expected-old-value update-ref in the
promotion step above, conditioned on the in-session parent-law PASS
under the frozen verdict rule. The PromotionReceipt appended afterward
(Construction-Receipt commit, receipt namespace only) is OUTPUT
EVIDENCE of this ceremony referencing the evidence object id — never an
input. Capability-level exclusivity remains unenforced (branch
unprotected); this is detection-grade governance, stated without
overclaim.

## scope

Valid for exactly one transition (BUILD-004). After BUILD-004 is
promoted, the corrected generational mechanism it realizes becomes the
authority for BUILD-005 admission with no further bootstrap exception.
