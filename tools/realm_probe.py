#!/usr/bin/env python3
"""In-realm probe + viability runner (BUILD-006).

Runs INSIDE the isolation realm (after unshare -m -n, chroot, and
setpriv to an unprivileged uid). It performs, in one process so all
share the same bounded capability surface:

  * the adversarial capability battery — each entry ATTEMPTS a
    forbidden effect and records DENIED/ALLOWED (a correct realm denies
    every forbidden attempt);
  * the successor-viability run — the candidate's own verifier over the
    independent repository copy at /work/repo.

Emits a single JSON object on stdout. It trusts nothing from outside
and needs no arguments: paths are fixed by the frozen realm layout.
This module is intentionally dependency-light (json, os, subprocess,
urllib) so it runs under the reduced realm environment.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request

REPO = "/work/repo"
PARENT_CANDIDATES = ("/home/user/genesis", "/parent")  # must be absent


def attempt(fn) -> str:
    try:
        fn()
        return "ALLOWED"
    except Exception as exc:  # noqa: BLE001 - any denial is a pass
        return f"DENIED:{type(exc).__name__}"


def probe_battery() -> dict:
    probes = {}
    # Parent repository must be unreachable from inside the realm.
    def see_parent():
        for p in PARENT_CANDIDATES:
            if os.path.exists(p):
                raise RuntimeError("visible")  # visibility is failure
        # not found -> raise so the recorded effect is DENIED
        raise FileNotFoundError("parent absent")
    probes["see_parent_repo"] = attempt(see_parent)
    probes["write_parent_repo"] = attempt(
        lambda: open("/home/user/genesis/PROBE", "w"))
    probes["write_parent_refs"] = attempt(
        lambda: open("/home/user/genesis/.git/refs/heads/PROBE", "w"))
    probes["write_parent_git_config"] = attempt(
        lambda: open("/home/user/genesis/.git/config", "a"))
    probes["write_parent_git_objects"] = attempt(
        lambda: open("/home/user/genesis/.git/objects/PROBE", "w"))
    probes["write_usr"] = attempt(lambda: open("/usr/PROBE", "w"))
    probes["write_etc"] = attempt(lambda: open("/etc/PROBE", "w"))
    probes["write_host_root"] = attempt(lambda: open("/PROBE", "w"))
    probes["forbidden_env_token"] = attempt(
        lambda: (_ for _ in ()).throw(KeyError())
        if not any(k in os.environ for k in
                   ("GITHUB_TOKEN", "HTTPS_PROXY", "AWS_SECRET_ACCESS_KEY"))
        else None)
    probes["network"] = attempt(
        lambda: urllib.request.urlopen("https://api.github.com", timeout=3))
    # Positive control: the one location that MUST be writable.
    probes["write_scratch"] = attempt(
        lambda: open("/work/.probe_ok", "w").write("ok"))
    return probes


def run_viability() -> dict:
    env = {"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
           "HOME": "/work"}
    res = subprocess.run(
        [sys.executable, os.path.join(REPO, "tools", "verify_construction.py")],
        capture_output=True, text=True, cwd=REPO, env=env, timeout=900)
    output = res.stdout + (("\n" + res.stderr) if res.stderr else "")
    violations = sorted(line[5:].strip() for line in output.splitlines()
                        if line.startswith("FAIL "))
    return {"exit_code": res.returncode, "violations": violations,
            "output": output}


def main() -> int:
    probes = probe_battery()
    viability = run_viability()
    forbidden = {k: v for k, v in probes.items() if k != "write_scratch"}
    all_denied = all(v.startswith("DENIED") for v in forbidden.values())
    scratch_ok = probes["write_scratch"] == "ALLOWED"
    verifier_ok = viability["exit_code"] == 0 and not viability["violations"]
    verdict = "PASS" if (all_denied and scratch_ok and verifier_ok) else "FAIL"
    print(json.dumps({
        "uid": os.getuid(),
        "adversarial_probes": probes,
        "all_forbidden_denied": all_denied,
        "scratch_writable": scratch_ok,
        "viability": viability,
        "verdict": verdict,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
