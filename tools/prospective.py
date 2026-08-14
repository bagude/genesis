#!/usr/bin/env python3
"""ProspectiveEvaluation — bounded successor-viability evaluator.
(BUILD-005, AUDIT-004 obligation 2.)

Unaccepted candidate code acquires no causal authority merely by being
selected for prospective evaluation. This operator runs the candidate's
own law over the candidate ONLY inside the frozen CapabilityEnvelope:

  * isolated disposable clone of the repository at the exact candidate
    commit, with every remote removed — no credential helpers, no push
    targets; candidate code that trashes refs trashes the clone's;
  * environment reduced to PATH plus a scratch HOME (env replacement,
    not inheritance) — no tokens, no proxy configuration;
  * network denied by OS namespace isolation (unshare -n), with an
    in-namespace probe run first so denial is MEASURED, not assumed;
  * the real repository's refs are snapshotted before and after and
    must compare equal.

The measured envelope is returned as evidence. A detached worktree is
NOT isolation and is not used here. This is process/namespace-level
bounding on a shared host, not an OS-image sandbox (declared
limitation, BUILD-005 non-claims).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import authority_lib as lib

ROOT = lib.ROOT
MINIMAL_PATH = "/usr/local/bin:/usr/bin:/bin"
NETWORK_PROBE = ("import urllib.request\n"
                 "urllib.request.urlopen('https://api.github.com', timeout=3)")


def real_repo_refs() -> str:
    return lib.git("for-each-ref", "--format=%(refname) %(objectname)")


def evaluate(candidate: str, transition: str = "?") -> dict:
    candidate_sha = lib.git("rev-parse", f"{candidate}^{{commit}}")
    scratch = Path(tempfile.mkdtemp(prefix="genesis-prospective-"))
    clone = scratch / "clone"
    home = scratch / "home"
    home.mkdir()
    env = {"PATH": MINIMAL_PATH, "HOME": str(home)}

    refs_before = real_repo_refs()
    lib.git("clone", "--quiet", str(ROOT), str(clone))
    subprocess.run(["git", "checkout", "--quiet", candidate_sha],
                   cwd=clone, capture_output=True, check=True)
    subprocess.run(["git", "remote", "remove", "origin"],
                   cwd=clone, capture_output=True)
    remotes = subprocess.run(["git", "remote"], cwd=clone,
                             capture_output=True, text=True).stdout.split()

    probe = subprocess.run(
        ["unshare", "-n", "--", sys.executable, "-c", NETWORK_PROBE],
        capture_output=True, env=env, timeout=60)
    network_denied = probe.returncode != 0

    res = subprocess.run(
        ["unshare", "-n", "--", sys.executable,
         str(clone / "tools" / "verify_construction.py")],
        capture_output=True, text=True, cwd=clone, env=env, timeout=900)
    output = res.stdout + (("\n" + res.stderr) if res.stderr else "")
    violations = sorted(line[5:].strip() for line in output.splitlines()
                        if line.startswith("FAIL "))
    refs_after = real_repo_refs()

    envelope = {
        "remotes": str(len(remotes)),
        "network_denied": "true" if network_denied else "false",
        "environment_vars": sorted(env),
        "real_repo_refs_unchanged":
            "true" if refs_before == refs_after else "false",
    }
    verdict = "PASS" if (res.returncode == 0 and not violations
                         and network_denied
                         and not remotes
                         and refs_before == refs_after) else "FAIL"
    return {
        "schema": "ProspectiveEvaluation/1",
        "transition": transition,
        "target_commit": candidate_sha,
        "verdict": verdict,
        "exit_code": res.returncode,
        "violations": violations,
        "capability_envelope": envelope,
        "environment_id": lib.environment_id(),
        "output": output,
    }


def main() -> int:
    candidate = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    transition = sys.argv[2] if len(sys.argv) > 2 else "?"
    result = evaluate(candidate, transition)
    env = result["capability_envelope"]
    print(f"prospective: verdict={result['verdict']} "
          f"target={result['target_commit'][:12]} "
          f"network_denied={env['network_denied']} "
          f"remotes={env['remotes']} "
          f"refs_unchanged={env['real_repo_refs_unchanged']} "
          f"violations={len(result['violations'])}")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
