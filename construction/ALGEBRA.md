# Construction Algebra — v1.4 (frozen by BUILD-000; amended by BUILD-001, BUILD-002, BUILD-003, BUILD-004)

## Principle

The build process does not *resemble* the laboratory's runtime loop; it
**instantiates the same abstract operator grammar under a different
ontology**.

Laboratory realization:

    M_t -> Proposal -> W_t -> Measurement -> Grounding -> M_{t+1}

Construction realization:

    B_t -> BuildProposal -> Repo_t -> Verification -> BuildGrounding -> B_{t+1}

where `B_t` is the current epistemic state of the builder/orchestrator
(the phase program, open questions, and accumulated grounding records),
and `Repo_t` is the authoritative repository state.

**Same operators, different realization.** The build-level operator is:

    Phi_B = F_B ∘ Pi_G^B ∘ R_B ∘ T̄_B ∘ I_{B->Repo} ∘ U_B

| Operator      | Laboratory meaning                  | Construction meaning                          |
|---------------|-------------------------------------|-----------------------------------------------|
| `U_B`         | model unfold -> proposal            | builder proposes an implementation increment  |
| `I_{B->Repo}` | transduction -> candidate action    | proposal becomes a concrete candidate patch   |
| `T̄_B`        | lawful world transition or reject   | repository law admits or rejects the patch    |
| `R_B`         | ruler measurement                   | canonical measurements of what happened       |
| `Pi_G^B`      | grounding projection                | the BuildGrounding record                     |
| `F_B`         | model fold                          | update of the phase program / next proposal   |

This algebra is itself law: **changes to this document require their own
BuildProposal.** The principle is immutable from Genesis onward:

    Propose difference -> lawfully realize it -> measure the resulting
    difference -> update the next proposal.

## Objects

### BuildProposal (`construction/proposals/BUILD-NNN.yaml`)

    P^B = (id, phase, goal, allowed_scope, prediction, non_claims, budget)

The prediction is the build analogue of the model predicting Δ̂R before
acting. It must be stated in mechanically checkable terms and committed
to the ledger **before** any realization work is committed.

`non_claims` bound the transition: what this increment deliberately does
NOT establish. They prevent scope inflation in the narrative.

### Candidate

The concrete patch (working-tree diff / commits) produced from the
proposal. A candidate is not a realized transition. `Proposal ≠
Candidate ≠ RealizedTransition ≠ GroundingRecord` — the construction
analogue of `p ≠ ã ≠ a ≠ e`.

### BuildGrounding (`construction/groundings/BUILD-NNN.yaml`)

    G^B = (proposal, predicted, observed, unexpected, evidence, decision)

- `predicted` must restate the proposal's prediction **verbatim** (the
  verifier enforces byte-equality of the mapping). A grounding may not
  quietly rewrite what was predicted.
- `observed` must cover every predicted key, and may add canonical
  measurements beyond them.
- `unexpected` is the honest channel: everything reality did that the
  prediction did not anticipate. An empty list is a claim, not a default.
- `decision.verdict` is `REALIZED` or `REJECTED`; `decision.next` names
  the successor proposal (the update to `B`).

## Law (admissibility of a construction transition)

A transition `Repo_t -> Repo_{t+1}` is admissible iff:

1. **Precedence.** The proposal exists in the ledger (a commit) before
   any realization commit for it. Prediction precedes action.
2. **Scope.** The realization diff touches only paths under
   `allowed_scope`.
3. **Budget.** Files changed across the transition ≤
   `budget.max_files_changed`.
4. **Verification.** Every predicted check is actually executed and its
   observed value recorded; `python3 tools/verify_construction.py`
   exits 0 over the whole construction ledger.
5. **Grounding.** The realization includes the BuildGrounding record in
   the same transition. No grounding, no realization.

## Rejection semantics

A failed increment is an event, not a mutation:

    Adm = 0  =>  Repo_{i+1} = Repo_i,  Ledger_{i+1} = Ledger_i ⊕ e^reject

Concretely: the candidate patch is **not merged**; a BuildGrounding with
`verdict: REJECTED` **is** committed (the ledger grows), and its
`unexpected` section updates the builder's epistemic state `B_i ->
B_{i+1}` — typically by revising the successor proposal. This is the
exact construction analogue of `w_{t+1} = w_t` under a rejected world
action with `L_{t+1} = L_t ⊕ e^reject`.

## Canonical measurements (`R_B`)

Measured from repository state and diff, never taken from the builder's
narrative:

- verifier exit code and per-check results
- test/typecheck results (once those laws exist; introduced by proposal)
- files changed, insertions, deletions for the transition
- scope conformance of the realization diff

## Amendment v1.1 — Measurement law (BUILD-001, from AUDIT-000)

> **No property is called measured unless `R_B` derives it from
> repository evidence.**

AUDIT-000 found `E_W = W_Δ − W_0 ≠ 0`: the v1 verifier enforced only
structural record law, while precedence, scope, and budget were
builder-reported. BUILD-001 closes this:

- **Attribution.** Every transition commit carries a
  `Construction-Transition: BUILD-NNN` trailer. The proposal commit is
  the commit adding the proposal file; it may touch only
  `construction/proposals/` and `construction/audits/`. Pre-BUILD-001
  commits are attributed by the record files they touch (grandfather
  clause).
- **Derived vocabulary.** The verifier derives, from git history and
  probe execution: `proposal_precedence_<id>` (strict git ancestry),
  `scope_conformance_<id>` (union of realization diffs vs
  allowed_scope + implicit record paths), `budget_conformance_<id>` and
  `files_changed_<id>` (distinct files across transition commits),
  `proposal_commit_<id>`, `probe_<name>` (probes declared in the
  proposal, executed by the verifier), `open_proposals`, and
  `untracked_commits`.
- **Format 2 groundings** (mandatory from BUILD-001): predicted and
  observed keys must be derived-vocabulary keys that match the derived
  values exactly, or carry a `reported_` prefix marking them as
  explicitly non-measured. `evidence.proposal_commit` must match the
  derived proposal commit.
- **Lifecycle.** A proposal without a grounding is `OPEN`. At most one
  OPEN proposal may exist, and it must be the highest-numbered. Statuses
  are `OPEN`, `REALIZED`, `REJECTED` — derived from the ledger, never
  declared.
- **No untracked transitions.** Every commit descending from the
  BUILD-001 realization must carry a transition trailer.
- **Independent attestation.** CI (`.github/workflows/construction.yml`)
  re-runs the verifier on every push; local and remote runs must agree.

External audits are archived under `construction/audits/` and enter the
ledger with the proposal commit of the transition that answers them.

## Amendment v1.2 — Governance closure (BUILD-002, from AUDIT-001)

> **A measuring instrument that executes proposal-controlled commands
> is itself an actuator. Measurement and Experiment are distinct
> operators with distinct capability sets.**

- **Measurement/Experiment separation.** The verifier is two operators:
  `R_B` (passive derivation over git evidence; executes nothing;
  `K_{R_B}^write = ∅`) and `E_B` (experiments). Probe definitions live
  only in the law-controlled registry `tools/probes.yaml`; proposals
  reference probes by name and can never inject a command. `E_B`
  executes in an ephemeral detached worktree — the authoritative tree
  is never an experiment's substrate — and isolation is attested by
  tree-status snapshot equality (`experiment_tree_isolation`).
- **Attribution freeze.** `Grounded(P_i) ⇒ Attribution(P_i)` is frozen
  at the commit adding `groundings/BUILD-i.yaml`; any attributed commit
  not ancestor-or-equal of that boundary is a violation
  (`attribution_extensions`). Historical derived measurements of closed
  transitions can therefore never change.
- **Record immutability.** `construction/proposals/`,
  `construction/groundings/`, `construction/audits/` are add-only over
  all history (`closed_record_mutations`); proposal commits may contain
  additions only. Records are amended by new records, never edited.
- **Canonical evidence identity.** From BUILD-002 onward,
  `evidence.proposal_commit` must equal the full 40-hex derived commit
  id exactly. BUILD-001's prefix relation is grandfathered as a closed
  record.

## Amendment v1.3 — Trust-boundary closure (BUILD-003, from AUDIT-002 / PRE-AUDIT-003)

> **A candidate that contains V_{t+1} may not use V_{t+1} as the
> authority that admits itself.**

Five causal roles, kept as distinct operators: `R_B` measurement,
`E_B` experiment, `V_B` verification (tools/verify_construction.py),
`G_B` authorization (tools/gate.py), `P_B` promotion (tools/promote.py).

- **Parent-law authorization.** `Accept(C_{t+1}) ⇒ V_t(C_{t+1}) = PASS`.
  `G_B` reads `tools/authority.yaml` from the ACCEPTED CANONICAL commit
  (never from the candidate), verifies member blob identities against
  the canonical tree, extracts exactly those members, and runs the
  parent verifier against the candidate's exact commit. The candidate's
  own law runs prospectively only. Law evolution without
  self-authorization: a candidate's grounding stays within the parent
  law's derived vocabulary; novel measurements enter as `reported_`
  once and become derived only for successors.
- **Fixed-point candidate + external GateReceipt.** In-candidate
  `reported_` gate keys are fixed-point hypotheses, never authority.
  The receipt is external to the candidate, binds
  `target_commit`/`target_tree`/`authority_identity`/verdicts/
  `environment_id`/probe evidence, and is what `P_B` consumes.
  Exact-target invariant: `Promote(C') ⇒ C' = receipt.target_commit`
  by full-SHA equality, with an atomic expected-old-value ref move.
- **Candidate/canonical separation.** Candidates live on
  `candidate/BUILD-NNN`; gate FAIL leaves canonical untouched and the
  attempt is preserved under `construction/rejections/`. CI on
  canonical is attestation, not authorization. Post-promotion, the
  receipt is appended under `construction/receipts/` in a receipt-only
  commit (trailer `Construction-Receipt: BUILD-NNN`, additions only,
  receipt namespaces only, excluded from transition attribution) —
  the authorized consequence of the promotion ceremony.
- **Closure-bound experiment evidence.** From BUILD-003, a transition's
  probe keys are matched against the evidence bound in its GateReceipt
  at closure; a present-time rerun is attestation and never redefines
  historical evidence. `experiment_tree_isolation` is narrowed to
  `authoritative_tree_status_preserved` (alias retained for closed
  records); `environment_id` is a first-class derived identity of the
  runtime surface.
- **Receipts are law from BUILD-004** (`RECEIPT_REQUIRED_FROM`);
  BUILD-003 is the declared bootstrap transition, its admission
  performed under the authority frozen in
  `construction/audits/PRE-AUDIT-003-BOOTSTRAP.md`.
- **Promotion exclusivity is law-with-detection, not prevention:**
  canonical mutations bypassing `P_B` are detected as permanent ledger
  violations; capability-level prevention requires platform branch
  protection (declared governance limitation).

## Amendment v1.4 — Evidence provenance (BUILD-004, from AUDIT-003)

> **Evidence content ≠ evidence provenance. A claim about a causal
> event is not evidence of that event merely because its fields are
> internally consistent.**

- **Causal coupling.** `P_B` accepts no verdict, receipt, or evidence
  inputs. It invokes the parent-law GateRun itself over the exact
  target and authorizes only from that in-process result:
  `Promote(C) ⇒ ActualParentLawExecution(C) = PASS`. Within the lawful
  path there is no route from fabricated PASS data to promotion.
- **Object ontology.** GateRun (process) → GateResult
  (content-addressed evidence object on `refs/construction/evidence`,
  emitted by `G_B` and committed BEFORE promotion; remote ref push is
  best-effort — where the platform denies non-branch ref pushes
  (observed HTTP 403, declared in BUILD-004-BOOTSTRAP-AMENDMENT-1),
  remote durability is provided by the in-history mirror under
  `construction/evidence/` appended with the receipt) →
  AuthorizationDecision (in-process, from the actual result) →
  Promote → PromotionReceipt (schema_version 2, referencing the
  GateResult evidence id; OUTPUT evidence, never authority) →
  PostPromotionAttestation (CI + full-ledger `V_B`). Receipt is
  evidence only.
- **Derived-only authority identities, rule v2.**
  `SHA256("authority-rule:v2\n" + "parent:<sha>\n" +
  "manifest:<blob>\n" + sorted "<blob> <path>" member lines + "\n")`,
  members verified against the parent tree before hashing, implemented
  once in `tools/authority_lib.py` and imported by `G_B`, `P_B`, and
  `V_B`. No digest is ever manually recorded. The identity binds
  parent canonical + manifest + member set, so a PASS under `A_t`
  cannot authorize under `A_{t+1}`.
- **Provenance-aware verification.** For schema-v2 receipts `V_B`
  recomputes the authority identity from git objects and requires the
  bound evidence object to exist and bind exactly the receipt's
  target, tree, parent canonical, authority, environment, verdict, and
  expected-violation set (`receipt_provenance_<id> = EVIDENCE_BOUND`).
  `--reproduce` re-executes the newest receipt's parent-law evaluation
  from frozen blobs and compares outcomes; CI runs it as independent
  attestation. BUILD-003's receipt remains
  `HISTORICAL_UNVERIFIED` and its bootstrap identity discrepancy
  (recorded `a498931e…` vs derived `38cbeab3…`) is surfaced as
  permanent derived measurements — archived in AUDIT-003, never
  normalized, closed records untouched.
- **Gate-compatible receipt law.** A closed transition ≥ BUILD-004
  requires a receipt only once canonical history extends beyond its
  closure commit (a finalized, unpromoted candidate cannot contain its
  own receipt — the V_BUILD-003 defect archived in
  BUILD-004-BOOTSTRAP).
- **Chronology.** `Finalize ≺ Evaluate ≺ Authorize ≺ Promote` is
  reconstructable from the remote evidence ref (pushed pre-promotion)
  and CI timestamps, not from builder prose. Rejected attempts keep
  their evidence objects and are preserved under
  `construction/rejections/`.
- **No overclaim.** Provenance rests on evidence binding, pre-promotion
  remote chronology, and reproducibility — not signatures. Promotion
  exclusivity remains detection, not prevention, until platform branch
  protection exists.

## Bootstrap note

BUILD-000 is self-hosting: its proposal predates the schema that
validates it, and the verifier it introduces is the instrument that
verifies it. This is the only transition permitted that exception; every
subsequent proposal is validated by law that already exists when it is
committed.
