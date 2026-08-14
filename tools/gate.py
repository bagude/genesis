#!/usr/bin/env python3
"""G_B — the Gate (parent-law evaluation). v2 (BUILD-004, AUDIT-003).

Performs the ACTUAL parent-law run and emits a content-addressed
GateResult evidence object on refs/construction/evidence. It writes no
receipts and grants nothing: authorization is P_B's decision, taken
only from a GateRun it invokes itself (causal coupling). The GateResult
is evidence of the run — never an authorization credential a caller
can supply.

Parent law = the authority manifest at the ACCEPTED CANONICAL commit
(never the candidate's copy): members verified by blob identity against
the parent tree, extracted by blob, overlaid on a detached worktree of
the exact candidate commit, and executed there.

The verdict rule supports a frozen expected-violation set (used by
declared bootstrap admissions where the parent law has a known,
archived defect): PASS iff the run's violation set equals exactly the
expected set (normally empty, meaning exit 0 and no violations).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import authority_lib as lib

ROOT = lib.ROOT


def resolve_exception_grant(parent_canonical: str,
                            transition: str) -> tuple[list[str], str]:
    """Resolve the AuthorizedExceptionGrant for a transition from the
    ACCEPTED parent canonical tree — the only lawful source of a
    nonempty expected-violation set (AUDIT-004 obligation 1). Returns
    (exception_set, grant_identity) where grant_identity is the grant
    file's blob sha, or ([], "NONE") when no grant exists. The invoker
    of P_B cannot mint a grant: it must already be part of accepted
    authority state."""
    rel = f"construction/exceptions/{transition}.yaml"
    try:
        blob = lib.git("rev-parse", f"{parent_canonical}:{rel}")
    except RuntimeError:
        return [], "NONE"
    grant = __import__("yaml").safe_load(
        lib.git("show", f"{parent_canonical}:{rel}"))
    exception_set = grant.get("exception_set")
    if not isinstance(exception_set, list):
        raise RuntimeError(f"{rel}: grant has no exception_set list")
    return sorted(str(v) for v in exception_set), blob


def run_parent_law(parent_canonical: str, candidate: str,
                   expected_violations: list[str] | None = None,
                   transition: str = "?",
                   emit_evidence: bool = True) -> dict:
    """Execute the parent law over the exact candidate commit. Returns
    the GateResult dict (including evidence commit id if emitted).

    `expected_violations` carries authority ONLY when it came from
    resolve_exception_grant (parent state) — G_B and P_B never accept
    it from a caller. V_B may pass a receipt's recorded set when
    REPRODUCING a historical evaluation; reproduction compares, it
    never authorizes."""
    expected = sorted(expected_violations or [])
    authority = lib.derive_authority_identity(parent_canonical)
    candidate_sha = lib.git("rev-parse", f"{candidate}^{{commit}}")
    candidate_tree = lib.git("rev-parse", f"{candidate_sha}^{{tree}}")

    scratch = Path(tempfile.mkdtemp(prefix="genesis-gaterun-"))
    worktree = scratch / "tree"
    try:
        lib.git("worktree", "add", "--detach", str(worktree), candidate_sha)
        for m in authority["members"]:
            target = worktree / m["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            blob = subprocess.run(["git", "cat-file", "blob", m["blob"]],
                                  capture_output=True, cwd=ROOT)
            if blob.returncode != 0:
                raise RuntimeError(f"cannot read blob for {m['path']}")
            target.write_bytes(blob.stdout)
        res = subprocess.run(
            [sys.executable, str(worktree / "tools" / "verify_construction.py")],
            capture_output=True, text=True, cwd=worktree, timeout=900)
        output = res.stdout + (("\n" + res.stderr) if res.stderr else "")
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree)],
                       capture_output=True, cwd=ROOT)

    violations = sorted(line[5:].strip() for line in output.splitlines()
                        if line.startswith("FAIL "))
    if expected:
        verdict = "PASS" if violations == expected else "FAIL"
    else:
        verdict = "PASS" if res.returncode == 0 and not violations else "FAIL"

    result = {
        "schema": "GateResult/1",
        "transition": transition,
        "target_commit": candidate_sha,
        "target_tree": candidate_tree,
        "parent_canonical": authority["parent_canonical"],
        "authority_identity": authority["identity"],
        "authority_rule": authority["rule"],
        "authority_serialization": authority["serialization"],
        "verdict": verdict,
        "exit_code": res.returncode,
        "violations": violations,
        "expected_violations": expected,
        "environment_id": lib.environment_id(),
    }
    if emit_evidence:
        result["evidence_object"] = lib.write_evidence(result, output)
    result["output"] = output
    return result


def main() -> int:
    # No policy arguments exist: the decision rule belongs to accepted
    # authority (base rule: zero expected violations), modified only by
    # an ExceptionGrant already present in the parent canonical tree.
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--transition", default="?")
    args = ap.parse_args()

    expected, grant_id = resolve_exception_grant(args.canonical,
                                                 args.transition)
    result = run_parent_law(args.canonical, args.candidate,
                            expected, args.transition)
    result["exception_grant"] = grant_id
    print(f"gate: verdict={result['verdict']} "
          f"target={result['target_commit'][:12]} "
          f"authority={result['authority_identity'][:16]} "
          f"evidence={result.get('evidence_object', 'none')[:12]} "
          f"violations={len(result['violations'])} "
          f"expected={len(result['expected_violations'])}")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
