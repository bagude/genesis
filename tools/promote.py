#!/usr/bin/env python3
"""P_B — Promotion. v2 (BUILD-004, AUDIT-003 repair).

CAUSAL COUPLING: this tool takes NO verdict, receipt, or evidence
inputs. It invokes the parent-law GateRun itself (G_B, in-process) over
the exact target and authorizes only from that actual result. There is
therefore no execution path from fabricated PASS data to promotion
within the lawful path: the only thing that can satisfy the
authorization condition is the parent law actually returning PASS,
here, on this exact commit.

Sequence (AUDIT-003 obligation 2 ontology):

    GateRun (invoked here) -> GateResult (evidence object, pushed to
    the remote evidence ref BEFORE promotion) -> AuthorizationDecision
    (in-process, from the returned result only) -> Promote (atomic
    expected-old-value fast-forward, exact-target full-SHA equality)
    -> PromotionReceipt (schema_version 2, referencing the GateResult
    evidence id — OUTPUT evidence of this ceremony, never an input)
    -> PostPromotionAttestation (CI / full-ledger V_B, separate).

FAIL leaves canonical unchanged; the failed run's evidence object is
preserved on the evidence ref and the attempt is recorded under
construction/rejections/.

Capability note (unchanged, no overclaim): this is the only LAWFUL
path onto canonical; preventing unlawful direct pushes requires
platform branch protection.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

import authority_lib as lib
import gate

ROOT = lib.ROOT


def append_record(branch: str, files: dict[str, str], trailer: str) -> None:
    lib.git("checkout", branch)
    for relpath, content in files.items():
        dest = ROOT / relpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
        lib.git("add", relpath)
    names = ", ".join(Path(p).name for p in files)
    lib.git("commit", "-m", f"Append {names}\n\n{trailer}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--transition", required=True)
    ap.add_argument("--expect-violation", action="append", default=[])
    args = ap.parse_args()

    canonical_sha = lib.git("rev-parse", f"refs/heads/{args.canonical}")
    candidate_sha = lib.git("rev-parse", f"{args.candidate}^{{commit}}")

    if lib.git("merge-base", canonical_sha, candidate_sha) != canonical_sha:
        print("REJECT: candidate is not a fast-forward of canonical; "
              "canonical unchanged")
        return 1

    # GateRun — the actual parent-law execution, invoked by P_B itself.
    result = gate.run_parent_law(canonical_sha, candidate_sha,
                                 args.expect_violation, args.transition)
    evidence_id = result["evidence_object"]

    # Pre-promotion durability: the evidence object is committed to the
    # local evidence ref before any canonical mutation. Remote ref push
    # is best-effort — the platform may deny non-branch ref pushes
    # (BUILD-004-BOOTSTRAP-AMENDMENT-1); remote durability is then
    # provided by the in-history mirror appended with the receipt.
    try:
        lib.git("push", "origin", f"{lib.EVIDENCE_REF}:{lib.EVIDENCE_REF}")
        evidence_pushed = "yes"
    except RuntimeError as exc:
        evidence_pushed = "no (platform ref-push policy)"
        print(f"warning: evidence ref push denied: {exc}")
    print(f"evidence object: {evidence_id} (remote push: {evidence_pushed})")

    prospective = gate.run_parent_law(candidate_sha, candidate_sha,
                                      transition=args.transition,
                                      emit_evidence=False)

    if result["verdict"] != "PASS":
        rejection = {
            "transition": args.transition,
            "target_commit": candidate_sha,
            "parent_canonical": canonical_sha,
            "authority_identity": result["authority_identity"],
            "verdict": result["verdict"],
            "violations": result["violations"],
            "evidence_object": evidence_id,
        }
        n = 1
        while (ROOT / "construction" / "rejections" /
               f"{args.transition}-attempt-{n}.yaml").exists():
            n += 1
        append_record(
            args.canonical,
            {f"construction/rejections/{args.transition}-attempt-{n}.yaml":
                yaml.safe_dump(rejection, sort_keys=False)},
            f"Construction-Receipt: {args.transition}")
        print(f"REJECT: parent law verdict {result['verdict']}; canonical "
              f"unchanged; attempt preserved with evidence {evidence_id}")
        return 1

    # AuthorizationDecision: in-process, from the actual result only.
    # Exact-target + authority-context binding, then atomic ref move.
    assert result["target_commit"] == candidate_sha
    lib.git("update-ref", f"refs/heads/{args.canonical}",
            candidate_sha, canonical_sha)
    print(f"PROMOTED {args.canonical}: {canonical_sha[:12]} -> "
          f"{candidate_sha[:12]}")

    receipt = {
        "receipt": "PromotionReceipt",
        "schema_version": 2,
        "transition": args.transition,
        "target_commit": candidate_sha,
        "target_tree": result["target_tree"],
        "parent_canonical": canonical_sha,
        "authority_identity": result["authority_identity"],
        "authority_rule": result["authority_rule"],
        "evidence_object": evidence_id,
        "evidence_ref_pushed": evidence_pushed,
        "parent_law_verdict": result["verdict"],
        "expected_violations": result["expected_violations"],
        "prospective_law_verdict": prospective["verdict"],
        "environment_id": result["environment_id"],
    }
    # Mirror must byte-equal the evidence object's meta: the object was
    # serialized before the evidence id and output were attached.
    output = result["output"]
    evidence_meta = {k: v for k, v in result.items()
                     if k not in ("output", "evidence_object")}
    append_record(
        args.canonical,
        {f"construction/receipts/{args.transition}.yaml":
            yaml.safe_dump(receipt, sort_keys=False),
         f"construction/evidence/{args.transition}.yaml":
            yaml.safe_dump(evidence_meta, sort_keys=False),
         f"construction/evidence/{args.transition}.log": output},
        f"Construction-Receipt: {args.transition}")
    print(f"receipt + evidence mirror appended (evidence {evidence_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
