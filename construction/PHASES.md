# Phase Program (builder epistemic state `B_t`)

Frozen ordering. Surface construction precedes the ruler because `R_O`
measures a world **through an interface-relative surface**, never an
observer-independent coordinate: `World -> Surface -> Ruler`.

| Phase | Name                                  | Exit condition (canonical)                                             | Status      |
|-------|---------------------------------------|------------------------------------------------------------------------|-------------|
| -1    | Construction algebra                  | Verifier enforces proposal/grounding law over the construction ledger   | REALIZED (BUILD-000; AUDIT-000 repair via BUILD-001 — measurement law closure, E_W → 0) |
| 0     | Genesis / contracts                   | Every later operator has a declared domain and codomain; meta-ontology frozen | PENDING (BUILD-002) |
| 1     | Ontology separation                   | Proposal ≠ CandidateAction ≠ Action ≠ Event; WorldState ≠ Observation; Measurement ≠ Grounding; ModelState ≠ WorldState — mechanically unavailable substitutions | PENDING |
| 2     | Deterministic world kernel            | Replay(w0, L_gov) = w_live for every generated legal sequence; Adm=0 ⇒ w' = w while ledger appends e_reject | PENDING |
| 3     | Epistemic surfaces                    | Two observers over the same world receive different surfaces: Π_E^A(w) ≠ Π_E^B(w) | PENDING |
| 4     | Ruler R, ΔR                           | R_O(W, Γ, Σ_O, Q_O) contract-relative; R_A(X) ≠ R_B(X) under different surfaces; R ≠ ΔR | PENDING |
| 5     | Causal + grounding interfaces         | Proposal -> CandidateAction without Proposal -> WorldMutation; Measurement -> Grounding without WorldState -> Model (leakage tests first-class) | PENDING |
| 6     | Deterministic model harness           | U_M, F_M scripted; both harnesses satisfy Observe -> Unfold -> Interact -> Fold -> Expose under disjoint ontologies | PENDING |
| 7     | Close recursive surface               | Persisted RecursiveEpisode η_t; Replay(η_t) = η_t deterministically      | PENDING |
| 8     | Prediction + grounding error          | Δ̂R before resolution; ε_R = d_R(Δ̂R, ΔR); dataset D_G accumulates       | PENDING |
| 9     | Audit / interface creation            | A_O acts on Γ; realized object is (Γ', Σ'_O, R'_O); ΔR_A = R'_O − R_O   | PENDING |
| 10    | Differential weighting                | J_W from audit responses; W_Δ inferred; W_0 declared separately; E_W = W_Δ − W_0 free to disagree | PENDING |
| 11    | Stochastic model                      | Swap U_M^scripted for U_{M,θ}; zero changes to T_W, L, K, R, Π_G        | PENDING |
| 12    | Adaptive grounded routing (harness MoE) | Routing over epistemic loci driven by measured R and realized W_Δ      | PENDING |

## World substrate decision (frozen with this program)

The first world is a **tiny causal graph**, not a generic graph:
`V = {A, B, C}`, scalar node states `x_A, x_B, x_C`, typed couplings
`A --γ_AB--> B --γ_BC--> C`, law as propagation `x_B' = f_AB(x_A, x_B)`,
`x_C' = f_BC(x_B, x_C)`. Interfaces determine which distinctions an
observer can access; capabilities determine which nodes/edges may be
perturbed. This substrate survives through Audit and weighting without
replacement.

## Kernel discipline (frozen with this program)

Python is the experimental language; the authoritative kernel is
deliberately boring: **pure reducers + frozen typed values + explicit
schemas + property tests**. Safety comes from making impossible
transitions *unavailable in the execution topology*, not from the type
checker alone. There must never exist a `world.apply(proposal)` path —
only `Proposal -> Decode -> CandidateAction -> Validate -> Authorize ->
Action -> Reduce`.
