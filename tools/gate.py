#!/usr/bin/env python3
"""G_B — the Gate (authorization). BUILD-003, PRE-AUDIT-003 semantics.

Authorizes a candidate under the PARENT law A_t, never under the law the
candidate itself carries. A_t's identity and membership are determined
exclusively by the accepted canonical state: this tool reads
tools/authority.yaml FROM THE CANONICAL COMMIT via git plumbing,
verifies each member's blob identity against the canonical tree,
extracts exactly those members, overlays them onto a detached worktree
of the candidate commit, and runs the parent verifier there. The
candidate's own manifest is never consulted for admission
(candidate_manifest_rule, PRE-AUDIT-003-BOOTSTRAP).

Output: a GateReceipt (YAML) written OUTSIDE the repository. The
receipt — not any claim inside the candidate — is what P_B consumes.
It binds: target commit and tree identity, authority identity,
parent-law verdict, prospective verdict, environment identity, and
closure-bound probe evidence.

Exit 0 iff the parent law admits the candidate.

Usage:
    python3 tools/gate.py --canonical <ref> --candidate <ref> \
        --receipt <path-outside-repo>
"""

from __future__ import annotations

import argparse
import hashlib
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def git(*args: str, cwd: Path = ROOT) -> str:
    res = subprocess.run(["git", *args], capture_output=True, text=True,
                         cwd=cwd)
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {res.stderr.strip()}")
    return res.stdout.strip()


def authority_members(canonical: str) -> list[dict]:
    manifest = yaml.safe_load(git("show", f"{canonical}:tools/authority.yaml"))
    members = manifest.get("members")
    if not isinstance(members, list) or not members:
        raise RuntimeError("canonical authority manifest has no members")
    return members


def authority_identity(members: list[dict]) -> str:
    lines = sorted(f"{m['blob']} {m['path']}" for m in members)
    return hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()


def environment_id() -> str:
    fingerprint = (f"python={platform.python_version()}"
                   f"|system={platform.system()}"
                   f"|pyyaml={yaml.__version__}")
    return hashlib.sha256(fingerprint.encode()).hexdigest()[:16]


def verify_and_extract(canonical: str, members: list[dict],
                       dest: Path) -> None:
    for m in members:
        path, blob = m["path"], m["blob"]
        actual = git("rev-parse", f"{canonical}:{path}")
        if actual != blob:
            raise RuntimeError(
                f"authority member {path} blob {actual} does not match "
                f"manifest {blob}")
        target = dest / path
        target.parent.mkdir(parents=True, exist_ok=True)
        content = subprocess.run(
            ["git", "cat-file", "blob", blob], capture_output=True, cwd=ROOT)
        if content.returncode != 0:
            raise RuntimeError(f"cannot read blob {blob} for {path}")
        target.write_bytes(content.stdout)


def run_verifier(worktree: Path) -> tuple[str, str]:
    res = subprocess.run(
        [sys.executable, str(worktree / "tools" / "verify_construction.py")],
        capture_output=True, text=True, cwd=worktree, timeout=600)
    verdict = "PASS" if res.returncode == 0 else "FAIL"
    return verdict, res.stdout


def probe_evidence(output: str) -> dict[str, str]:
    evidence = {}
    for line in output.splitlines():
        m = re.match(r"derived (probe_\S+) = (\S+)", line)
        if m:
            evidence[m.group(1)] = m.group(2)
    return evidence


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--receipt", required=True)
    args = ap.parse_args()

    receipt_path = Path(args.receipt).resolve()
    if str(receipt_path).startswith(str(ROOT)):
        print("FAIL receipt path must be outside the repository")
        return 1

    canonical = git("rev-parse", args.canonical)
    candidate = git("rev-parse", args.candidate)
    candidate_tree = git("rev-parse", f"{candidate}^{{tree}}")

    members = authority_members(canonical)
    auth_id = authority_identity(members)

    scratch = Path(tempfile.mkdtemp(prefix="genesis-gate-"))
    parent_wt = scratch / "parent-law"
    prospective_wt = scratch / "prospective"
    try:
        git("worktree", "add", "--detach", str(parent_wt), candidate)
        verify_and_extract(canonical, members, parent_wt)
        parent_verdict, parent_out = run_verifier(parent_wt)

        git("worktree", "add", "--detach", str(prospective_wt), candidate)
        prospective_verdict, _ = run_verifier(prospective_wt)
    finally:
        for wt in (parent_wt, prospective_wt):
            subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                           capture_output=True, cwd=ROOT)

    receipt = {
        "receipt": "GateReceipt",
        "target_commit": candidate,
        "target_tree": candidate_tree,
        "authority_canonical": canonical,
        "authority_identity": auth_id,
        "authority_members": members,
        "parent_law_verdict": parent_verdict,
        "prospective_law_verdict": prospective_verdict,
        "environment_id": environment_id(),
        "probe_evidence": probe_evidence(parent_out),
        "issuer": "A_t parent law bundle executed by gate ceremony",
    }
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False))
    print(f"gate: parent_law_verdict={parent_verdict} "
          f"prospective={prospective_verdict} target={candidate[:12]} "
          f"receipt={receipt_path}")
    return 0 if parent_verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
