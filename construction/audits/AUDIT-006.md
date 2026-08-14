# AUDIT-006 — External audit of BUILD-006 realization (received 2026-08-14)

**Verdict on BUILD-006: REALIZED_WITH_CERTIFICATION_GAPS**

BUILD-006 closed most of AUDIT-005 (independent `--no-local` storage;
mount/network/chroot realm; uid 65534; adversarial probes; first-class
capability evidence; schema-v4 receipts certifying from bound evidence;
honestly weakened chronology; attempt 1 rejected and preserved; green
verification and CI). Four blocking problems remain. BUILD-007 is the
Phase -1 repair; Phase 0 moves to BUILD-008.

## Central discoveries

    CapabilityIsolation != CapabilityIsolationEvidence
                        != CapabilityIsolationCertification

    CandidateState != AcceptedState

    A denied effect != a probe that happened to throw an exception

The realm may be stronger than its measurements. The state tested before
promotion is not necessarily the state that becomes authoritative after
governance evidence and receipt material are appended.

## Findings

1. **Privilege escalation is not mechanically closed.** The realm reduces
   privilege (`setpriv --reuid/--regid --clear-groups`) but never freezes
   `no_new_privs`, nor clears inheritable/ambient capabilities or the
   bounding set, nor establishes that setuid/setgid/file-capability
   execution over the read-only host `/usr`, `/bin`, `/lib`, `/lib64`,
   `/etc` mounts cannot reacquire privilege. `CurrentUID = nobody` does
   not establish `FuturePrivilege ≤ CurrentPrivilege` for every
   reachable executable.
2. **`see_parent_repo` probe has unsound semantics.** It raises
   `RuntimeError("visible")` when the parent IS visible; the generic
   wrapper converts any exception to `DENIED:<Type>`; the certification
   treats every `DENIED*` as PASS. A visible parent would therefore
   CERTIFY. Generally: `ExceptionRaised ≠ ForbiddenEffectDenied`.
3. **Host-after rulers overclaim.** `parent_worktree_unchanged` derives
   from `HEAD^{tree}` — committed tree identity, blind to uncommitted
   worktree modification. `parent_objects_unchanged` derives from object
   COUNT — equal count does not imply equal object content. Neither
   ruler measures the property its name asserts.
4. **CandidateState ≠ AcceptedState.** BUILD-006 attempt 1 proved this
   empirically: parent gate PASS, payload viability PASS, isolation
   certified — yet the successor's own verifier rejected the state after
   receipt and evidence mirrors were appended, forcing rollback. So
   `V_{t+1}(CandidateState) = PASS` does not imply
   `V_{t+1}(AcceptedCanonicalState) = PASS`.

## Hard obligations for BUILD-007

1. Privilege monotonicity: for every candidate-controlled exec
   transition, `PrivilegeAfter ≤ PrivilegeBefore`, via no_new_privs,
   empty inheritable/ambient/bounding sets, nosuid semantics, and
   adversarial escalation probes. Claim only what is enforced and
   measured — never full kernel isolation.
2. Typed probe outcomes (`DENIED` / `ALLOWED` / `ERROR` /
   `INCONCLUSIVE`) with explicit precondition, attempted effect, and
   denial/success/error predicates per probe; PASS only on the specific
   expected denial semantics. Every probe audited for false-pass paths.
3. Ruler/claim correspondence: strengthen the measurements (real
   worktree-content integrity over a declared scope; real object-store
   content integrity), declare Scope and Metric, and name the claim for
   exactly what is measured. The measurement must not mutate the
   protected state.
4. Successor viability must cover the state that actually inherits
   authority: either stage the exact would-be accepted state and verify
   it before canonical mutation (Option A, preferred, requiring
   `Hash(Stage) = Hash(FinalAcceptedState)`), or make payload viability
   and canonical viability first-class, preregistered, evidence-backed
   gates (Option B) with defined provisionality and rollback.

Additionally: freeze an explicit authority-transfer state machine —
"promotion" currently conflates ref movement, payload installation,
receipt append, successor-law activation, and authority inheritance.
`Authority_{t+1}` must not become active before the state it governs has
passed successor viability.

## Standing limitations to preserve

- Remote CI (GitHub hosted runner) cannot create the namespace realm
  (`unshare` → Operation not permitted). It may establish parent-law
  reproduction, successor semantic conformance, receipt/evidence
  integrity, and static capability-policy conformance — never remote
  reproduction of the local capability realm.
- Canonical and evidence branches remain unprotected: internal
  governance detection ≠ platform-level write prevention.

## Inspection measurements (builder, 2026-08-14, pre-freeze)

- Accepted state 44effdd…: ledger verifies, 0 violations.
- Finding 2 reproduced: a probe raising `RuntimeError` on a VISIBLE
  parent yields `DENIED:RuntimeError`, certified as PASS. Confirmed
  false-negative path.
- Privilege primitives available and effective: `setpriv
  --no-new-privs --bounding-set=-all --inh-caps=-all` inside the realm
  yields, from `/proc/self/status`: `NoNewPrivs 1`, `CapInh`, `CapPrm`,
  `CapEff`, `CapBnd`, `CapAmb` all `0000000000000000`, uid/gid 65534.
  `nosuid,nodev` bind remount flags accepted. This is the BUILD-007
  privilege mechanism.

## Disposition

    BUILD-006 — REALIZED_WITH_CERTIFICATION_GAPS (records immutable)
    BUILD-007 — Phase -1 AUDIT-006 repair
    BUILD-008 — Phase 0 Genesis/contracts, only after BUILD-007 passes
                external audit
