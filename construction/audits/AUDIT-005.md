# AUDIT-005 — External audit of BUILD-005 realization (received 2026-08-14)

**Verdict on BUILD-005: REALIZED_WITH_CAPABILITY_GAPS**

BUILD-005 closed most of AUDIT-004 (no caller PASS redefinition;
ExceptionGrant from parent authority; dual gate; payload/ledger split;
remote evidence branch; parent-law reproduction in CI). The claimed
prospective capability boundary is nonetheless incomplete. BUILD-006 is
the Phase -1 repair; Phase 0 moves to BUILD-007.

## Central discovery

    InterfaceIsolation != CapabilityIsolation

Removing network, remotes, credentials, and inherited environment
shrinks a candidate's causal surface but does not prove
K_candidate^write(parent) = ∅ while writable shared substrate remains.
A capability is not absent merely because the preferred interface to
exercise it was removed. Isolation is a property of reachable causal
effects, not of directory layout.

## Findings

1. **Local clone may share writable git object storage.** BUILD-005's
   evaluator used `git clone <local> <scratch>`, which hard-links
   objects. DisposableClone != IndependentSubstrate; the
   refs_before == refs_after check does not detect object-store
   effects.
2. **Network namespace does not isolate the host filesystem.**
   `unshare -n` denies network only; candidate Python ran in the host
   mount namespace and could reach arbitrary user-writable paths.
   NetworkDenied does not entail FilesystemAuthority bounded.
3. **Receipt capability envelope not bound to viability evidence.** The
   v6 verifier checked receipt envelope fields and separately bound the
   evidence target/verdict, but never required structural equality
   between Receipt.capability_envelope and
   ProspectiveEvaluation.capability_envelope — recreating
   ReportedMeasurement != MeasuredReality.
4. **Successor viability not independently reproduced by CI.** CI
   reproduced the parent GateRun only.
5. **REMOTE_PRE_PROMOTION overclaims.** The verifier derives it from
   present-day graph membership (evidence ∈ ancestors(branch tip)),
   which proves RemoteEvidencePresent, not
   RemoteEvidenceExistedBeforePromotion; a post-promotion push would
   satisfy the same check.

## Hard obligations for BUILD-006

1. Prospective storage causally independent of parent writable
   substrate (no hard-linked objects, no shared worktree/metadata/refs/
   object store); tested by adversarial mutation probe, not path
   inequality.
2. Real filesystem/process capability boundary:
   K_prospective_write(parent_repo) = ∅,
   K_prospective_write(governance_state) = ∅,
   K_prospective_write(host_outside_scratch) = ∅, or a precise smaller
   contract proven exactly.
3. Adversarial capability probes in the contract: attempts to mutate
   parent refs/files/config/objects, read forbidden env, access
   network, write outside scratch — each must be DENIED, recorded as
   evidence, without risking the authoritative repo.
4. Certified capability envelope derived from the bound prospective
   evidence object, not from receipt assertion; duplicates require
   exact equality. Evidence binds candidate identity, evaluator
   identity/version, capability-policy identity, environment, measured
   effects, viability verdict.
5. Remote attestation reproduces BOTH gates; define invariant vs
   environment-relative vs informational fields; if CI cannot supply
   the isolation primitive, say so and use a conformance probe rather
   than calling it exact reproduction.
6. Chronology terminology must match evidence: distinguish
   REMOTE_EVIDENCE_PRESENT from a pre-promotion-attested status; mark
   PRE_PROMOTION_CHRONOLOGY = UNATTESTED absent an externally-ordered
   platform event.

## Inspection measurements (builder, 2026-08-14, pre-freeze)

- Accepted state b36fd08…: ledger verifies, 0 violations.
- Finding 1 confirmed: default `git clone` of the repo produced 211
  hard-linked objects in the clone's object store; `git clone
  --no-local` produced 0. Shared writable substrate was real.
- Isolation primitives: `bwrap` ABSENT; `unshare`, `setpriv`, `chroot`
  present; session holds privilege to create mount/net namespaces.
- Realm proven (unshare -m -n → RO bind /usr,/bin,/lib,/lib64,/etc →
  chroot → setpriv nobody): from inside, parent repo path is
  non-existent (see_parent_repo DENIED:FileNotFoundError), /usr and
  /etc writes DENIED (read-only), / write DENIED (unprivileged uid),
  only /work writable (ALLOWED), network DENIED; process uid 65534;
  host parent repo intact afterward. This is the BUILD-006 mechanism.
- CI (GitHub Actions) may lack namespace privilege; BUILD-006 defines a
  conformance fallback there rather than claiming identical isolation.
- Branch protection: canonical and evidence branches both unprotected
  (owner action pending). detection != prevention preserved.

## Disposition

    BUILD-005 — REALIZED_WITH_CAPABILITY_GAPS (records immutable)
    BUILD-006 — Phase -1 AUDIT-005 repair
    BUILD-007 — Phase 0 Genesis/contracts, only after BUILD-006 passes
                external audit
