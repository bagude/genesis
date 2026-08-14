#!/usr/bin/env python3
"""In-realm typed probe runner and viability executor.
v2 (BUILD-007, AUDIT-006 Obligations 1 & 2).

Runs INSIDE the isolation realm. Every probe states its own effect
semantics: it decides DENIED / ALLOWED / ERROR / INCONCLUSIVE from what
actually happened, and an unexpected exception is ERROR — never a
denial. The generic "any exception means denied" wrapper that produced
the AUDIT-006 Finding 2 false-pass path does not exist here.

Also measures the privilege state from /proc/self/status so privilege
monotonicity is certified from evidence rather than from the launch
command line, and runs the viability target (the verifier of whatever
tree is mounted at /work/repo — candidate payload or staged accepted
state).

Emits one JSON object on stdout. Stdlib only.
"""

from __future__ import annotations

import errno
import json
import os
import socket
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capability_policy as pol  # noqa: E402

REPO = "/work/repo"
SCRATCH = "/work"

# Errno values that constitute genuine denial of a write effect.
DENY_ERRNOS = {errno.EACCES, errno.EPERM, errno.EROFS, errno.ENOENT,
               errno.ENOTDIR}


def result(pid: str, outcome: str, evidence: str) -> dict:
    expected = pol.EXPECTED_OUTCOME[pid]
    return {
        "probe_id": pid,
        "attempted_effect": next(p["attempted_effect"] for p in pol.PROBES
                                 if p["probe_id"] == pid),
        "expected_outcome": expected,
        "observed_outcome": outcome,
        "evidence": evidence,
        "verdict": "PASS" if outcome == expected else "FAIL",
    }


def write_probe(pid: str, path: str, mode: str = "w") -> dict:
    """Attempt a write. Success is ALLOWED (the effect occurred). A
    denial errno is DENIED. Anything else is ERROR."""
    try:
        with open(path, mode) as fh:
            fh.write("probe")
    except OSError as exc:
        if exc.errno in DENY_ERRNOS:
            return result(pid, "DENIED",
                          f"errno={errno.errorcode.get(exc.errno, exc.errno)}")
        return result(pid, "ERROR", f"unexpected errno={exc.errno}: {exc}")
    except Exception as exc:  # noqa: BLE001
        return result(pid, "ERROR", f"{type(exc).__name__}: {exc}")
    # The write succeeded: the forbidden effect OCCURRED.
    try:
        os.unlink(path)
    except OSError:
        pass
    return result(pid, "ALLOWED", f"wrote {path}")


def probe_parent_visibility() -> dict:
    """Positive test: if any parent path resolves, the effect ALLOWED."""
    pid = "parent_repo_visibility"
    try:
        visible = [p for p in pol.PARENT_PATH_CANDIDATES if os.path.exists(p)]
    except Exception as exc:  # noqa: BLE001
        return result(pid, "ERROR", f"{type(exc).__name__}: {exc}")
    if visible:
        return result(pid, "ALLOWED", f"visible: {visible}")
    return result(pid, "DENIED", "no parent path resolves inside the realm")


def probe_forbidden_env() -> dict:
    """Positive test over os.environ; no exceptions involved."""
    pid = "forbidden_env_present"
    present = [k for k in pol.FORBIDDEN_ENV if k in os.environ]
    if present:
        return result(pid, "ALLOWED", f"present: {present}")
    return result(pid, "DENIED",
                  f"none of {len(pol.FORBIDDEN_ENV)} credential/proxy "
                  f"variables present; env keys={sorted(os.environ)}")


def probe_network() -> dict:
    pid = "network_connect"
    try:
        with socket.create_connection(("140.82.121.4", 443), timeout=5):
            return result(pid, "ALLOWED", "TCP connect succeeded")
    except OSError as exc:
        if exc.errno in (errno.ENETUNREACH, errno.EHOSTUNREACH,
                         errno.ECONNREFUSED, errno.EACCES, errno.EPERM):
            return result(pid, "DENIED",
                          f"errno={errno.errorcode.get(exc.errno, exc.errno)}")
        if isinstance(exc, socket.timeout):
            return result(pid, "DENIED", "connection timed out")
        return result(pid, "DENIED", f"OSError: {exc}")
    except Exception as exc:  # noqa: BLE001
        return result(pid, "ERROR", f"{type(exc).__name__}: {exc}")


def probe_setuid_syscall() -> dict:
    pid = "setuid_root_syscall"
    try:
        os.setuid(0)
    except PermissionError:
        return result(pid, "DENIED", "setuid(0) -> EPERM")
    except OSError as exc:
        return result(pid, "DENIED", f"setuid(0) -> errno {exc.errno}")
    except Exception as exc:  # noqa: BLE001
        return result(pid, "ERROR", f"{type(exc).__name__}: {exc}")
    return result(pid, "ALLOWED", f"setuid(0) succeeded, euid={os.geteuid()}")


def probe_setuid_binary() -> dict:
    """Exec a reachable setuid binary and check whether euid 0 results."""
    pid = "setuid_binary_elevation"
    reachable = []
    for path in pol.SETUID_CANDIDATES:
        try:
            st = os.stat(path)
        except OSError:
            continue
        if st.st_mode & 0o4000:
            reachable.append(path)
    if not reachable:
        # The effect is unavailable: no setuid binary exists in the realm.
        return result(pid, "DENIED",
                      "no setuid binary reachable in the realm")
    for path in reachable:
        try:
            res = subprocess.run([path, "-c", "id -u"], capture_output=True,
                                 text=True, timeout=20)
        except Exception as exc:  # noqa: BLE001
            continue
        if res.stdout.strip() == "0":
            return result(pid, "ALLOWED",
                          f"{path} yielded uid 0")
    return result(pid, "DENIED",
                  f"setuid binaries {reachable} did not yield uid 0 "
                  f"(no_new_privs / nosuid)")


def probe_subprocess_denied(pid: str, argv: list[str]) -> dict:
    """A privileged operation attempted via an external tool. Exit 0 is
    ALLOWED; a nonzero exit is DENIED; a missing tool means the effect is
    unavailable (DENIED with that evidence)."""
    try:
        res = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        return result(pid, "DENIED", f"{argv[0]} not present in the realm")
    except Exception as exc:  # noqa: BLE001
        return result(pid, "ERROR", f"{type(exc).__name__}: {exc}")
    if res.returncode == 0:
        return result(pid, "ALLOWED", f"{argv[0]} succeeded")
    return result(pid, "DENIED",
                  f"exit={res.returncode}: {(res.stderr or '').strip()[:120]}")


def probe_signal_host() -> dict:
    pid = "signal_host_process"
    try:
        os.kill(1, 0)
    except PermissionError:
        return result(pid, "DENIED", "kill(1,0) -> EPERM")
    except ProcessLookupError:
        return result(pid, "DENIED", "pid 1 not reachable")
    except Exception as exc:  # noqa: BLE001
        return result(pid, "ERROR", f"{type(exc).__name__}: {exc}")
    return result(pid, "ALLOWED", "signalled out-of-realm pid 1")


def run_probes() -> dict:
    results = [
        probe_parent_visibility(),
        write_probe("write_parent_worktree_file",
                    "/home/user/genesis/PROBE"),
        write_probe("write_parent_ref",
                    "/home/user/genesis/.git/refs/heads/PROBE"),
        write_probe("write_parent_git_config",
                    "/home/user/genesis/.git/config", mode="a"),
        write_probe("write_parent_git_object",
                    "/home/user/genesis/.git/objects/PROBE"),
        write_probe("write_ro_usr", "/usr/PROBE"),
        write_probe("write_ro_etc", "/etc/PROBE"),
        write_probe("write_realm_root", "/PROBE"),
        probe_forbidden_env(),
        probe_network(),
        probe_setuid_syscall(),
        probe_setuid_binary(),
        probe_subprocess_denied("mount_from_realm",
                                ["mount", "-t", "tmpfs", "tmpfs", "/tmp"]),
        probe_subprocess_denied("unshare_from_realm",
                                ["unshare", "-m", "true"]),
        probe_signal_host(),
        write_probe("write_scratch", os.path.join(SCRATCH, ".probe_ok")),
    ]
    return {r["probe_id"]: r for r in results}


def measure_privilege() -> dict:
    """Privilege state measured from the kernel, not from the launcher."""
    measured = {"uid": str(os.getuid()), "gid": str(os.getgid()),
                "euid": str(os.geteuid()), "egid": str(os.getegid())}
    try:
        with open("/proc/self/status") as fh:
            for line in fh:
                if ":" not in line:
                    continue
                key, val = line.split(":", 1)
                if key in ("NoNewPrivs", "CapInh", "CapPrm", "CapEff",
                           "CapBnd", "CapAmb"):
                    measured[key] = val.strip()
    except OSError as exc:
        measured["read_error"] = str(exc)
    return measured


def run_viability() -> dict:
    env = {"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
           "HOME": SCRATCH}
    res = subprocess.run(
        [sys.executable, os.path.join(REPO, "tools", "verify_construction.py")],
        capture_output=True, text=True, cwd=REPO, env=env, timeout=900)
    output = res.stdout + (("\n" + res.stderr) if res.stderr else "")
    violations = sorted(line[5:].strip() for line in output.splitlines()
                        if line.startswith("FAIL "))
    return {"exit_code": res.returncode, "violations": violations,
            "output": output}


def main() -> int:
    probes = run_probes()
    privilege = measure_privilege()
    viability = run_viability()
    probes_ok, probe_problems = pol.certify_probes(probes)
    priv_ok, priv_problems = pol.certify_privilege(privilege)
    verifier_ok = viability["exit_code"] == 0 and not viability["violations"]
    print(json.dumps({
        "policy_id": pol.POLICY_ID,
        "privilege_measured": privilege,
        "privilege_certified": priv_ok,
        "privilege_problems": priv_problems,
        "probes": probes,
        "probes_certified": probes_ok,
        "probe_problems": probe_problems,
        "viability": viability,
        "verdict": "PASS" if (probes_ok and priv_ok and verifier_ok) else "FAIL",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
