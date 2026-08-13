# Construction Algebra — v1.1 (frozen by BUILD-000; amended by BUILD-001)

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

## Bootstrap note

BUILD-000 is self-hosting: its proposal predates the schema that
validates it, and the verifier it introduces is the instrument that
verifies it. This is the only transition permitted that exception; every
subsequent proposal is validated by law that already exists when it is
committed.
