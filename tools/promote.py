#!/usr/bin/env python3
"""P_B — Promotion. BUILD-003, PRE-AUDIT-003 semantics.

Consumes ONLY the external GateReceipt — never any claim inside the
candidate. Enforces the exact-target invariant and then, and only then,
moves the canonical ref:

    Promote(C') => C' = receipt.target_commit   (full-SHA equality)
    receipt.parent_law_verdict == PASS
    receipt.authority_identity == identity recomputed from the
        canonical manifest at promotion time

The ref move is a fast-forward performed atomically with an
expected-old-value check, so a concurrent canonical mutation aborts the
promotion instead of being overwritten. After promotion, the receipt is
appended to the ledger as construction/receipts/BUILD-NNN.yaml in a
receipt-only commit carrying the "Construction-Receipt: BUILD-NNN"
trailer — the authorized consequence of this ceremony, restricted to
the receipt namespace (receipt_append_authorization,
PRE-AUDIT-003-BOOTSTRAP).

Promotion exclusivity is law-with-detection: this tool is the only
LAWFUL path onto canonical; capability-level exclusivity requires
platform branch protection (declared limitation).

Usage:
    python3 tools/promote.py --receipt <file> --canonical <branch> \
        --transition BUILD-NNN
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def git(*args: str) -> str:
    res = subprocess.run(["git", *args], capture_output=True, text=True,
                         cwd=ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {res.stderr.strip()}")
    return res.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--canonical", required=True)
    ap.add_argument("--transition", required=True)
    args = ap.parse_args()

    receipt = yaml.safe_load(Path(args.receipt).read_text())
    target = receipt.get("target_commit", "")
    verdict = receipt.get("parent_law_verdict")
    claimed_auth = receipt.get("authority_identity")

    if verdict != "PASS":
        print(f"REJECT: parent_law_verdict={verdict}; canonical unchanged")
        return 1

    canonical_sha = git("rev-parse", args.canonical)
    # Recompute authority identity from the canonical manifest NOW —
    # the receipt's claim must match accepted parent state.
    manifest = yaml.safe_load(
        git("show", f"{canonical_sha}:tools/authority.yaml"))
    lines = sorted(f"{m['blob']} {m['path']}" for m in manifest["members"])
    actual_auth = hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()
    if claimed_auth != actual_auth:
        print(f"REJECT: receipt authority {claimed_auth} does not match "
              f"canonical authority {actual_auth}; canonical unchanged")
        return 1

    if git("rev-parse", target) != target:
        print("REJECT: receipt target is not a full canonical object id")
        return 1
    if git("merge-base", canonical_sha, target) != canonical_sha:
        print("REJECT: target is not a fast-forward of canonical; "
              "canonical unchanged")
        return 1

    # Exact-target, atomic, fast-forward-only ref move.
    git("update-ref", f"refs/heads/{args.canonical}", target, canonical_sha)
    print(f"PROMOTED {args.canonical}: {canonical_sha[:12]} -> {target[:12]}")

    # Authorized receipt append (receipt namespace only).
    git("checkout", args.canonical)
    dest = ROOT / "construction" / "receipts" / f"{args.transition}.yaml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(Path(args.receipt).read_text())
    git("add", str(dest.relative_to(ROOT)))
    git("commit", "-m",
        f"Append GateReceipt for {args.transition}\n\n"
        f"Construction-Receipt: {args.transition}")
    print(f"receipt appended: {dest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
