# BUILD-004-BOOTSTRAP-AMENDMENT-1 — Amended bootstrap authority (append-only)

Amends construction/audits/BUILD-004-BOOTSTRAP.md after the lawful
rejection of candidate attempt 1 (construction/rejections/
BUILD-004-attempt-1.yaml). The original record is immutable; this
amendment is frozen BEFORE any new candidate is finalized, preserving
Identity(A_004_bootstrap) ≺ Finalize(C_004').

## Why amendment is required

1. The frozen expected-violation set was wrong. The parent law
   V_BUILD-003 has a SECOND unrepresentable structure beyond the
   receipt law: pre-proposal audit-record commits. AUDIT-003's own
   protocol ordering (archive audit → freeze bootstrap → preregister
   proposal) places two attributed commits before the proposal commit,
   which V_BUILD-003's precedence law necessarily reads as
   "realization before proposal", cascading into two grounding
   contradictions. The gate run over attempt 1 therefore produced four
   violations against the one frozen, and correctly FAILED the
   candidate. Attempt 1's own v5 carried the same precedence defect —
   the rejection was substantively correct, not merely procedural: the
   defective candidate must not be promoted.
2. The frozen mechanism required pushing refs/construction/evidence to
   the remote BEFORE promotion. The platform push policy denies
   non-branch ref pushes from this environment (HTTP 403, observed and
   recorded in the attempt-1 rejection). Pre-promotion REMOTE evidence
   durability is not achievable here.

## Attempt-1 evidence mirror (local evidence object fbcee211…)

    schema: GateResult/1
    transition: BUILD-004
    target_commit: 83873e6441fc004beb76778d251cb658de8e9137
    parent_canonical: bfe2fc9fcf2a3cd3aeda9dc918002272ae22371a
    authority_identity (rule v2, derived):
        b970394efc9f132155190eb59f1f7ad9ea282c2a4fd953f3a5abaa6bb57adb20
    verdict: FAIL
    violations: the four listed in the rejection record
    environment_id: 05fb1d1e8f917bec

## Amended provisions (all else in BUILD-004-BOOTSTRAP unchanged)

### A. parent_canonical_identity (superseding)

The commit that adds THIS amendment record — a descendant of the
rejection-record commit 0a639c35529988d3d6aebc4590f25ffbf957768c. The
new candidate/BUILD-004 branches from exactly that commit. Full SHA
reported at freeze completion; derivable forever as this file's adding
commit.

### B. Frozen expected-violation set for the parent-law run (superseding)

parent_law_verdict = PASS iff the violation set of the V_BUILD-003
bundle run over the finalized candidate equals EXACTLY these four
strings and nothing else:

    BUILD-004: closed transition has no promotion receipt (required from BUILD-004)
    BUILD-004: proposal commit is not a strict ancestor of all realization commits
    construction/groundings/BUILD-004.yaml.observed: 'proposal_precedence_BUILD-004: PASS' contradicts derived value 'FAIL'
    construction/groundings/BUILD-004.yaml.predicted: 'proposal_precedence_BUILD-004: PASS' contradicts derived value 'FAIL'

All four are mechanical consequences of the two archived parent-law
defects (receipt law; pre-proposal audit-record commits). The successor
law in the new candidate must repair both so that BUILD-005 admission
requires no expected-violation exception. The candidate's own
prospective law must yield ZERO violations on the finalized candidate.

### C. Evidence durability (superseding the pre-promotion remote push)

The GateResult evidence object is committed to the LOCAL
refs/construction/evidence before promotion (content-addressed; its id
enters the ceremony records). Remote pre-promotion durability being
platform-blocked, remote durability is provided by mirroring the
evidence meta (and run log) into the in-history record namespace
construction/evidence/ in the post-promotion receipt commit, where
record-immutability law applies. Chronology evidence therefore rests
on: the content-addressed evidence id referenced by the receipt, CI
reproduction of the evaluation from in-history objects, and this
declared limitation — NOT on remote ref ordering. This deviation is
declared, not silent.

### D. Verifier fallback

Successor law reads evidence objects from refs/construction/evidence
when available and falls back to the construction/evidence/ mirror —
required for CI and fresh clones, which cannot fetch the unpushed ref.

## Scope

Valid for the remainder of the BUILD-004 transition only. Everything
else in BUILD-004-BOOTSTRAP.md (issuer, executor, evaluation bundle
blob identities, authority rule v2, causal coupling, FAIL semantics,
no-overclaim) remains in force.
