#!/usr/bin/env python3
"""P_B — Promotion. v3 (BUILD-005, AUDIT-004 repair).

NO POLICY ARGUMENTS. The caller cannot supply expected, accepted,
ignored, or waived failures, nor alternate verdict rules. The effective
decision rule is:

    EffectiveDecisionRule = BaseDecisionRule (zero expected violations)
                            ⊕ AuthorizedExceptionGrant

where the grant, if any, is resolved by G_B from the ACCEPTED parent
canonical tree (construction/exceptions/<transition>.yaml). The invoker
of P_B cannot mint one.

Dual gate (AUDIT-004 obligation 3): promotion requires

    ParentLaw(C) = PASS  AND  SuccessorViability(C) = PASS

Parent evaluation runs first and executes only accepted-law code over
candidate data; parent FAIL rejects WITHOUT ever executing candidate
code. Successor viability runs the candidate's own law strictly inside
the bounded CapabilityEnvelope (tools/prospective.py): isolated
credential-free clone, minimal environment, OS-enforced network
denial, measured evidence. The parent remains the admitting authority;
the successor never authorizes itself — but a successor that cannot
validate its own proposed accepted state does not become the next
authority.

Payload vs governance ledger (AUDIT-004 obligation 5):

    Reject(C)  => PayloadState' = PayloadState
                  GovernanceLedger' = GovernanceLedger ⊕ RejectionEvent
    Promote(C) => PayloadState' = CandidatePayload

A rejection DOES advance the canonical commit (the ledger append); it
never changes the payload coordinate. This tool says exactly that.

Chronology (AUDIT-004 obligation 4, Option A): evidence objects are
pushed to the remote governance branch claude/genesis-evidence BEFORE
promotion; if that push fails the receipt's chronology_status is
downgraded to CHRONOLOGY_UNATTESTED explicitly, never silently.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

import authority_lib as lib
import gate
import prospective

ROOT = lib.ROOT
EVIDENCE_BRANCH = "claude/genesis-evidence"


def append_record(branch: str, files: dict[str, str], trailer: str) -> None:
    lib.git("checkout", branch)
    for relpath, content in files.items():
        dest = ROOT / relpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
        lib.git("add", relpath)
    names = ", ".join(Path(p).name for p in files)
    lib.git("commit", "-m", f"Append {names}\n\n{trailer}")


def push_evidence() -> str:
    """Best-effort pre-promotion push of the evidence chain to the
    remote governance BRANCH (non-branch ref pushes are platform-
    denied). Returns the chronology status this ceremony can honestly
    claim."""
    try:
        lib.git("push", "origin",
                f"{lib.EVIDENCE_REF}:refs/heads/{EVIDENCE_BRANCH}")
        # Honest: presence on the remote branch, NOT pre-promotion
        # ordering (AUDIT-005 obligation 6). The verifier derives this
        # independently; the receipt value is informational only.
        return "REMOTE_EVIDENCE_PRESENT"
    except RuntimeError as exc:
        print(f"warning: evidence branch push failed: {exc}")
        return "REMOTE_EVIDENCE_ABSENT"


def reject(canonical: str, transition: str, records: dict) -> None:
    n = 1
    while (ROOT / "construction" / "rejections" /
           f"{transition}-attempt-{n}.yaml").exists():
        n += 1
    append_record(
        canonical,
        {f"construction/rejections/{transition}-attempt-{n}.yaml":
            yaml.safe_dump(records, sort_keys=False)},
        f"Construction-Receipt: {transition}")
    print("REJECT: payload state unchanged; governance ledger appended "
          "the rejection event")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--transition", required=True)
    args = ap.parse_args()

    canonical_sha = lib.git("rev-parse", f"refs/heads/{args.canonical}")
    candidate_sha = lib.git("rev-parse", f"{args.candidate}^{{commit}}")
    if lib.git("merge-base", canonical_sha, candidate_sha) != canonical_sha:
        print("REJECT: candidate is not a fast-forward of canonical")
        return 1

    # Decision rule from accepted authority only.
    expected, grant_id = gate.resolve_exception_grant(canonical_sha,
                                                      args.transition)

    # Gate 1: parent admission (accepted code over candidate data).
    parent = gate.run_parent_law(canonical_sha, candidate_sha,
                                 expected, args.transition)
    chronology = push_evidence()
    if parent["verdict"] != "PASS":
        reject(args.canonical, args.transition, {
            "transition": args.transition,
            "target_commit": candidate_sha,
            "parent_canonical": canonical_sha,
            "authority_identity": parent["authority_identity"],
            "parent_law_verdict": parent["verdict"],
            "violations": parent["violations"],
            "exception_grant": grant_id,
            "successor_viability_verdict":
                "NOT_EVALUATED (parent FAIL: candidate code not executed)",
            "evidence_object": parent["evidence_object"],
            "chronology_status": chronology,
        })
        return 1

    # Gate 2: successor viability, bounded capability surface only.
    viability = prospective.evaluate(candidate_sha, args.transition)
    viability_meta = {k: v for k, v in viability.items() if k != "output"}
    viability_evidence = lib.write_evidence(viability_meta,
                                            viability["output"])
    chronology = push_evidence()
    if viability["verdict"] != "PASS":
        reject(args.canonical, args.transition, {
            "transition": args.transition,
            "target_commit": candidate_sha,
            "parent_canonical": canonical_sha,
            "parent_law_verdict": parent["verdict"],
            "successor_viability_verdict": viability["verdict"],
            "viability_violations": viability["violations"],
            "capability_envelope": viability["capability_envelope"],
            "exception_grant": grant_id,
            "evidence_object": parent["evidence_object"],
            "viability_evidence_object": viability_evidence,
            "chronology_status": chronology,
        })
        return 1

    # AuthorizationDecision: both actual results, in-process.
    assert parent["target_commit"] == candidate_sha
    lib.git("update-ref", f"refs/heads/{args.canonical}",
            candidate_sha, canonical_sha)
    print(f"PROMOTED {args.canonical}: payload {canonical_sha[:12]} -> "
          f"{candidate_sha[:12]}")

    receipt = {
        "receipt": "PromotionReceipt",
        "schema_version": 4,
        "transition": args.transition,
        "target_commit": candidate_sha,
        "target_tree": parent["target_tree"],
        "parent_canonical": canonical_sha,
        "authority_identity": parent["authority_identity"],
        "authority_rule": parent["authority_rule"],
        "evidence_object": parent["evidence_object"],
        "viability_evidence_object": viability_evidence,
        "parent_law_verdict": parent["verdict"],
        "expected_violations": parent["expected_violations"],
        "exception_grant": grant_id,
        "successor_viability_verdict": viability["verdict"],
        "capability_policy_id": viability.get("capability_policy_id"),
        # Duplicate of the certified envelope for convenience; V_B
        # requires exact equality with the bound evidence object and
        # certifies from the evidence, never from this copy.
        "capability_envelope": viability.get("capability_envelope"),
        "chronology_status": chronology,
        "prepromotion_chronology": "UNATTESTED",
        "environment_id": parent["environment_id"],
    }
    parent_meta = {k: v for k, v in parent.items()
                   if k not in ("output", "evidence_object")}
    append_record(
        args.canonical,
        {f"construction/receipts/{args.transition}.yaml":
            yaml.safe_dump(receipt, sort_keys=False),
         f"construction/evidence/{args.transition}.yaml":
            yaml.safe_dump(parent_meta, sort_keys=False),
         f"construction/evidence/{args.transition}.log": parent["output"],
         f"construction/evidence/{args.transition}-viability.yaml":
            yaml.safe_dump(viability_meta, sort_keys=False),
         f"construction/evidence/{args.transition}-viability.log":
            viability["output"]},
        f"Construction-Receipt: {args.transition}")
    print(f"receipt + evidence mirrors appended "
          f"(gate {parent['evidence_object'][:12]}, "
          f"viability {viability_evidence[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
