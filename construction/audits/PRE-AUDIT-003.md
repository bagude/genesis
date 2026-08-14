# PRE-AUDIT-003 — Pre-realization constraints on BUILD-003 (received 2026-08-14)

Proposal ordering and scope PASS; BUILD-003 lawfully OPEN, no
implementation occurred. Architecture directionally accepted;
realization blocked until these semantics are explicitly resolved.
The frozen BUILD-003 proposal is not modified by this record.

## Constraints and binding resolutions

### 1. Authorization target identity / grounding circularity

Constraint: GateReceipt.target = C; Promote(C') => C' = GateReceipt.target.
No candidate modification after authorization; no "observed PASS"
before the observation exists.

Resolution (fixed-point candidate + external receipt):
- In-candidate reported_ gate keys are fixed-point HYPOTHESES ("the
  gate run on exactly this candidate returns PASS"), marked
  non-measured by the reported_ prefix; never authority.
- The GateReceipt is EXTERNAL to the candidate and never enters it:
  {target_commit (full sha), target_tree, authority_identity, verdict,
  environment_id, probe evidence}.
- Ordering: candidate finalized -> G_B gates that exact commit ->
  P_B promotes iff receipt.verdict = PASS and receipt.target_commit
  equals the candidate commit by full-SHA equality -> receipt appended
  post-promotion as construction/receipts/BUILD-NNN.yaml in a distinct
  receipt commit (trailer Construction-Receipt; add-only namespace;
  excluded from transition attribution).
- Gate FAIL: canonical untouched; attempt preserved under
  construction/rejections/ with the receipt; the candidate's internal
  hypothesis dies with the rejected candidate.
- V reconciles in-candidate reported_ gate keys against receipts
  permanently; mismatch is a violation.

### 2. Parent authority bundle

Constraint: A_t = (V_t, G_t, P_t, manifest); identity and membership
determined by accepted parent state, never by candidate A_{t+1}.

Resolution: tools/authority.yaml AT THE ACCEPTED CANONICAL HEAD
enumerates bundle members with git blob hashes. G_B reads the manifest
from the canonical commit via plumbing, extracts exactly the listed
members from the canonical tree, verifies blob hashes before use.
The candidate's manifest is never consulted for admission. BUILD-003
remains a declared bootstrap (A_t = V_BUILD-002 bundle at 409be0c,
applied by this procedure, recorded reported_); mechanical law from
BUILD-004 onward.

### 3. Promotion exclusivity

Resolution (honest split):
- Enforceable: P_B checks authorization; V requires every closed
  transition >= BUILD-004 to have a receipt binding its final commit,
  so canonical mutations bypassing P_B are DETECTED as permanent
  ledger violations.
- Not enforceable by BUILD-003: capability-level exclusivity. Push
  access can mutate canonical; prevention requires platform controls
  (branch protection, required checks) outside the ledger's causal
  reach — declared as a capability/governance limitation and
  recommended to the repository owner as an operator action.

### 4. Reported verdict is not authority

Resolution: P_B consumes only the external GateReceipt. In-candidate
reported_ values exist to satisfy prediction-coverage law and are
reconciled against receipts by V after the fact. The proposal phrase
"recorded as reported_ evidence" is fixed to mean: the candidate's
non-authoritative echo; authority lives only in G_B's independently
bound receipt.

## Disposition

All four constraints are entailed by the preregistered mechanism once
its unspecified points (evidence localization, manifest, ordering) are
pinned as above. No material change to the frozen proposal; BUILD-003
stands. These resolutions are binding realization semantics for
BUILD-003 and law from BUILD-004.
