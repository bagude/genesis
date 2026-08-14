#!/usr/bin/env python3
"""Shared authority/evidence library (BUILD-004, AUDIT-003 repair).

Single source of truth for:

  * authority identity derivation, rule v2 — identities are ALWAYS
    derived from actual git objects, never manually recorded
    (AUDIT-003 Finding 1);
  * environment identity;
  * GateResult evidence objects on refs/construction/evidence —
    content-addressed, durable, created before promotion so that
    Finalize < Evaluate < Authorize < Promote is reconstructable
    (AUDIT-003 obligation 5).

Imported by gate.py (G_B), promote.py (P_B), and
verify_construction.py (V_B) so all three share one derivation.
"""

from __future__ import annotations

import hashlib
import platform
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_REF = "refs/construction/evidence"
AUTHORITY_RULE = "v2"


def git(*args: str, cwd: Path | None = None, input_bytes: bytes | None = None) -> str:
    res = subprocess.run(["git", *args], capture_output=True,
                         cwd=cwd or ROOT, input=input_bytes)
    if res.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)}: {res.stderr.decode(errors='replace').strip()}")
    return res.stdout.decode().strip()


def environment_id() -> str:
    """Runtime-surface fingerprint (not an OS image identity)."""
    fingerprint = (f"python={platform.python_version()}"
                   f"|system={platform.system()}"
                   f"|pyyaml={yaml.__version__}")
    return hashlib.sha256(fingerprint.encode()).hexdigest()[:16]


def authority_serialization(parent_canonical: str, manifest_blob: str,
                            members: list[dict]) -> str:
    """Canonical serialization, rule v2. Versioned, deterministic,
    unambiguous; binds parent canonical state, manifest identity, and
    the sorted member set."""
    lines = sorted(f"{m['blob']} {m['path']}" for m in members)
    return (f"authority-rule:{AUTHORITY_RULE}\n"
            f"parent:{parent_canonical}\n"
            f"manifest:{manifest_blob}\n"
            + "\n".join(lines) + "\n")


def derive_authority_identity(parent_canonical: str) -> dict:
    """Derive A_t identity from actual git objects at the parent
    canonical commit. Verifies every manifest member's blob against the
    parent tree before hashing; raises on any mismatch."""
    parent = git("rev-parse", f"{parent_canonical}^{{commit}}")
    manifest_blob = git("rev-parse", f"{parent}:tools/authority.yaml")
    manifest = yaml.safe_load(git("show", f"{parent}:tools/authority.yaml"))
    members = manifest.get("members")
    if not isinstance(members, list) or not members:
        raise RuntimeError("authority manifest has no members")
    for m in members:
        actual = git("rev-parse", f"{parent}:{m['path']}")
        if actual != m["blob"]:
            raise RuntimeError(
                f"authority member {m['path']}: tree blob {actual} != "
                f"manifest blob {m['blob']}")
    ser = authority_serialization(parent, manifest_blob, members)
    return {
        "parent_canonical": parent,
        "manifest_blob": manifest_blob,
        "members": members,
        "serialization": ser,
        "identity": hashlib.sha256(ser.encode()).hexdigest(),
        "rule": AUTHORITY_RULE,
    }


def write_evidence(meta: dict, log_text: str) -> str:
    """Commit a content-addressed GateResult evidence object to the
    evidence ref. Returns the evidence commit id. The object is
    external to any candidate tree."""
    meta_blob = git("hash-object", "-w", "--stdin",
                    input_bytes=yaml.safe_dump(meta, sort_keys=False).encode())
    log_blob = git("hash-object", "-w", "--stdin",
                   input_bytes=log_text.encode())
    tree_desc = (f"100644 blob {meta_blob}\tmeta.yaml\n"
                 f"100644 blob {log_blob}\toutput.log\n")
    tree = git("mktree", input_bytes=tree_desc.encode())
    try:
        parent = git("rev-parse", "--verify", "--quiet", EVIDENCE_REF)
    except RuntimeError:
        parent = ""
    args = ["commit-tree", tree, "-m",
            f"GateResult {meta.get('transition', '?')} "
            f"target={meta.get('target_commit', '?')}"]
    if parent:
        args += ["-p", parent]
    commit = git(*args)
    if parent:
        git("update-ref", EVIDENCE_REF, commit, parent)
    else:
        git("update-ref", EVIDENCE_REF, commit)
    return commit


def read_evidence(evidence_commit: str) -> dict:
    """Load the meta of an evidence object; raises if absent."""
    return yaml.safe_load(git("show", f"{evidence_commit}:meta.yaml"))
