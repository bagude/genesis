# AUDIT-000 — External audit of BUILD-000 (received 2026-08-13)

Audited object: the realized repository state after BUILD-000, examined
directly rather than through the build narrative.

**Verdict: REALIZED_BOOTSTRAP / AUDIT_REPAIR_REQUIRED**

## Principal discrepancy

The algebra declares precedence, scope, budget, verification, and
grounding as construction admissibility laws. The realized verifier
enforces only structural schema/cross-record properties. It does not
derive scope conformance, changed-file budget, proposal-before-
realization precedence, probe execution, or evidence validity from
repository state.

Values such as `scope_conformance: PASS` were therefore *reported*
measurements, not measurements independently produced by `R_B`.

Formally, with `W_0` = declared construction law and `W_Δ` = realized
verifier behavior:

    E_W = W_Δ − W_0 ≠ 0.

## Findings

| # | Result       | Finding                                                        |
|---|--------------|----------------------------------------------------------------|
| 1 | PASS         | proposal causally precedes BUILD-000 realization                |
| 2 | PASS         | realized BUILD-000 transition conforms to declared scope        |
| 3 | PASS         | realized transition is within declared file budget              |
| 4 | FAIL         | scope law is not mechanically derived by verifier               |
| 5 | FAIL         | budget law is not mechanically derived by verifier              |
| 6 | FAIL         | precedence law is not mechanically verified                     |
| 7 | FAIL         | predicted probes are not themselves executed/attested by verifier |
| 8 | SUSPECT      | evidence provenance reported but not independently validated    |
| 9 | SUSPECT      | unresolved-proposal lifecycle lacks explicit semantic distinction |
| 10| INCONCLUSIVE | no independent CI status reproduces the local verifier result   |

## Constraint imposed on the successor proposal

The findings are not repair instructions. The successor must establish:

> **No property is called measured unless `R_B` derives it from
> repository evidence.**

and must decide how to mechanically ground: ProposalPrecedence,
ScopeConformance, BudgetConformance, ProbeResults, EvidenceProvenance —
preregistering the mechanism and its predicted verification effects
before implementing, then returning the proposal/realization/grounding
sequence for another external audit.

## Disposition

Incorporated as BUILD-001 (audit repair / measurement law closure).
Phase 0 (Genesis / contracts) moves to BUILD-002.
