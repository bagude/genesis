#!/usr/bin/env python3
"""P_B — Publication and authority transfer. v4 (BUILD-007, AUDIT-006).

No policy arguments: the decision rule belongs to accepted authority
(base rule ∅ expected violations ⊕ an ExceptionGrant resolved by G_B
from the parent canonical tree). P_B invokes the parent-law GateRun
itself, so no caller-supplied verdict can authorize anything.

AUDIT-006 Obligation 4 — the state that inherits authority is the state
that gets verified. Frozen state machine:

    CANDIDATE_FINALIZED
      -> PARENT_ADMITTED           V_t(C) PASS, accepted code only
      -> SUCCESSOR_PAYLOAD_VIABLE  V_{t+1}(C) in the bounded realm
      -> FINAL_STATE_STAGED        commit S = C + receipt + evidence
                                   mirrors, built WITHOUT touching the
                                   canonical ref (git plumbing)
      -> SUCCESSOR_CANONICAL_VIABLE V_{t+1}(S) in the bounded realm
      -> AUTHORIZED
      -> PUBLISHED / AUTHORITY_TRANSFERRED

Hash(Stage) = Hash(FinalAcceptedState) holds by construction: publication
fast-forwards canonical to exactly S and appends NOTHING afterwards. The
CanonicalViability evidence object is external (evidence ref/branch), so
recording it cannot perturb S.

AUTHORITY TRANSFER EVENT = the single atomic expected-old-value
update-ref publishing S. Before it, A_t is authoritative and S is
provisional; after it, A_{t+1} governs. Any gate failure ⇒ no ref
movement ⇒ PayloadState unchanged, while the GovernanceLedger may append
a RejectionEvent. Capability-level exclusivity is not claimed: the
branch is unprotected, so this is the only LAWFUL path, not the only
physically possible one.
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


def push_evidence() -> str:
    """Push the evidence chain to the remote governance BRANCH (non-branch
    ref pushes are platform-denied). Returns the honest chronology status:
    presence on the remote, never pre-promotion ordering."""
    try:
        lib.git("push", "origin",
                f"{lib.EVIDENCE_REF}:refs/heads/{EVIDENCE_BRANCH}")
        return "REMOTE_EVIDENCE_PRESENT"
    except RuntimeError as exc:
        print(f"warning: evidence branch push failed: {exc}")
        return "REMOTE_EVIDENCE_ABSENT"


def stage_final_state(base: str, files: dict[str, str],
                      transition: str) -> str:
    """Build commit S on top of `base` containing exactly `files`, using
    plumbing only — no branch, no checkout, no canonical mutation. S is
    the exact would-be accepted state."""
    import os
    import subprocess

    # Build the tree in a scratch index so the working index and the
    # working tree are never touched by staging.
    tmp_index = ROOT / ".git" / f"index.stage.{transition}"
    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = str(tmp_index)

    def g(*args: str) -> str:
        res = subprocess.run(["git", *args], capture_output=True, cwd=ROOT,
                             env=env)
        if res.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: "
                               f"{res.stderr.decode(errors='replace')}")
        return res.stdout.decode().strip()

    try:
        g("read-tree", base)
        for relpath, content in files.items():
            blob = subprocess.run(["git", "hash-object", "-w", "--stdin"],
                                  input=content.encode(), capture_output=True,
                                  cwd=ROOT, env=env)
            blob_sha = blob.stdout.decode().strip()
            g("update-index", "--add", "--cacheinfo",
              f"100644,{blob_sha},{relpath}")
        tree = g("write-tree")
    finally:
        if tmp_index.exists():
            tmp_index.unlink()
    return lib.git("commit-tree", tree, "-p", base, "-m",
                   f"Append PromotionReceipt and evidence mirrors for "
                   f"{transition}\n\nConstruction-Receipt: {transition}")


def reject(canonical: str, transition: str, record: dict) -> None:
    """PayloadState unchanged; GovernanceLedger appends the event."""
    n = 1
    while (ROOT / "construction" / "rejections" /
           f"{transition}-attempt-{n}.yaml").exists():
        n += 1
    lib.git("checkout", canonical)
    dest = ROOT / "construction" / "rejections" / f"{transition}-attempt-{n}.yaml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(yaml.safe_dump(record, sort_keys=False))
    lib.git("add", str(dest.relative_to(ROOT)))
    lib.git("commit", "-m", f"Append rejection record for {transition} "
                            f"attempt {n}\n\n"
                            f"Construction-Receipt: {transition}")
    print("REJECT: payload state unchanged (no authority transferred); "
          "governance ledger appended the rejection event")


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

    expected, grant_id = gate.resolve_exception_grant(canonical_sha,
                                                      args.transition)

    # --- PARENT_ADMITTED: accepted code only; candidate code not run yet.
    parent = gate.run_parent_law(canonical_sha, candidate_sha, expected,
                                 args.transition)
    chronology = push_evidence()
    if parent["verdict"] != "PASS":
        reject(args.canonical, args.transition, {
            "transition": args.transition, "state": "PARENT_ADMISSION_FAILED",
            "target_commit": candidate_sha, "parent_canonical": canonical_sha,
            "authority_identity": parent["authority_identity"],
            "parent_law_verdict": parent["verdict"],
            "violations": parent["violations"],
            "exception_grant": grant_id,
            "successor_payload_viability": "NOT_EVALUATED "
                                           "(candidate code not executed)",
            "evidence_object": parent["evidence_object"],
            "chronology_status": chronology,
        })
        return 1

    # --- SUCCESSOR_PAYLOAD_VIABLE: candidate law over candidate payload.
    payload = prospective.evaluate(candidate_sha, args.transition, "payload")
    payload_meta = {k: v for k, v in payload.items() if k != "output"}
    payload_ev = lib.write_evidence(payload_meta, payload.get("output", ""))
    chronology = push_evidence()
    if payload["verdict"] != "PASS":
        reject(args.canonical, args.transition, {
            "transition": args.transition, "state": "PAYLOAD_VIABILITY_FAILED",
            "target_commit": candidate_sha, "parent_canonical": canonical_sha,
            "parent_law_verdict": parent["verdict"],
            "payload_viability_verdict": payload["verdict"],
            "payload_problems": (payload.get("probe_problems", []) +
                                 payload.get("privilege_problems", [])),
            "violations": payload.get("violations"),
            "evidence_object": parent["evidence_object"],
            "payload_viability_evidence_object": payload_ev,
            "chronology_status": chronology,
        })
        return 1

    # --- FINAL_STATE_STAGED: build the exact would-be accepted state.
    receipt = {
        "receipt": "PromotionReceipt",
        "schema_version": 5,
        "transition": args.transition,
        "target_commit": candidate_sha,
        "target_tree": parent["target_tree"],
        "parent_canonical": canonical_sha,
        "authority_identity": parent["authority_identity"],
        "authority_rule": parent["authority_rule"],
        "evidence_object": parent["evidence_object"],
        "payload_viability_evidence_object": payload_ev,
        "parent_law_verdict": parent["verdict"],
        "expected_violations": parent["expected_violations"],
        "exception_grant": grant_id,
        "successor_payload_viability_verdict": payload["verdict"],
        "canonical_viability": "EXTERNAL_EVIDENCE",
        "capability_policy_id": payload["capability_policy_id"],
        "capability_policy_blob": payload["capability_policy_blob"],
        "privilege_measured": payload["privilege_measured"],
        "capability_envelope": payload["capability_envelope"],
        "integrity_before": payload["integrity_before"],
        "integrity_after": payload["integrity_after"],
        "chronology_status": chronology,
        "prepromotion_chronology": "UNATTESTED",
        "authority_transfer_event": "PUBLISH_REF_UPDATE",
        "environment_id": parent["environment_id"],
    }
    t = args.transition
    staged_files = {
        f"construction/receipts/{t}.yaml": yaml.safe_dump(receipt,
                                                          sort_keys=False),
        f"construction/evidence/{t}.yaml": yaml.safe_dump(
            {k: v for k, v in parent.items()
             if k not in ("output", "evidence_object")}, sort_keys=False),
        f"construction/evidence/{t}.log": parent["output"],
        f"construction/evidence/{t}-payload-viability.yaml": yaml.safe_dump(
            payload_meta, sort_keys=False),
        f"construction/evidence/{t}-payload-viability.log":
            payload.get("output", ""),
    }
    staged = stage_final_state(candidate_sha, staged_files, t)
    # The staged state must be REF-REACHABLE to be independently
    # evaluable — `git clone --no-local` transfers only reachable
    # objects — while remaining NON-CANONICAL, so its existence confers
    # no authority (BUILD-007-BOOTSTRAP-AMENDMENT-2). The staging branch
    # lives only across the canonical-viability window and is deleted
    # afterwards whatever the verdict.
    staging_ref = f"refs/heads/staged/{t}"
    lib.git("update-ref", staging_ref, staged)
    print(f"FINAL_STATE_STAGED: {staged} (staging ref {staging_ref}, "
          f"non-canonical)")

    # --- SUCCESSOR_CANONICAL_VIABLE: the state that will inherit authority.
    try:
        canonical_v = prospective.evaluate(staged, t, "canonical")
    finally:
        try:
            lib.git("update-ref", "-d", staging_ref)
        except RuntimeError as exc:
            print(f"warning: staging ref cleanup failed: {exc}")
    cv_meta = {k: v for k, v in canonical_v.items() if k != "output"}
    cv_meta["staged_state_commit"] = staged
    cv_ev = lib.write_evidence(cv_meta, canonical_v.get("output", ""))
    chronology = push_evidence()
    if canonical_v["verdict"] != "PASS":
        reject(args.canonical, t, {
            "transition": t, "state": "CANONICAL_VIABILITY_FAILED",
            "target_commit": candidate_sha, "staged_state_commit": staged,
            "parent_canonical": canonical_sha,
            "parent_law_verdict": parent["verdict"],
            "payload_viability_verdict": payload["verdict"],
            "canonical_viability_verdict": canonical_v["verdict"],
            "violations": canonical_v.get("violations"),
            "evidence_object": parent["evidence_object"],
            "payload_viability_evidence_object": payload_ev,
            "canonical_viability_evidence_object": cv_ev,
            "chronology_status": chronology,
            "note": "no authority was transferred: canonical ref never moved",
        })
        return 1

    # --- AUTHORIZED -> PUBLISHED (the authority-transfer event).
    lib.git("update-ref", f"refs/heads/{args.canonical}", staged,
            canonical_sha)
    lib.git("checkout", args.canonical)
    lib.git("reset", "--hard", staged)
    print(f"AUTHORITY_TRANSFERRED: payload {canonical_sha[:12]} -> "
          f"{candidate_sha[:12]}, accepted state = staged {staged[:12]} "
          f"(canonical viability evidence {cv_ev[:12]}, external)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
