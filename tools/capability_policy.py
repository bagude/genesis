#!/usr/bin/env python3
"""Frozen capability policy (BUILD-007, AUDIT-006 repair).

ONE authority for what the prospective realm claims and how each claim
is measured, so no second implementation can drift from the certificate:

  * PRIVILEGE_CONTRACT — the privilege state that must hold INSIDE the
    realm, measured from /proc/self/status (Obligation 1).
  * PROBES — typed adversarial probe DECLARATIONS: probe_id,
    attempted_effect, expected_outcome. Outcomes are effect semantics,
    never exception semantics (Obligation 2).
  * INTEGRITY_RULERS — each ruler's exact SCOPE and METRIC, so a
    certified name states what was measured (Obligation 3).

Stdlib-only and dependency-free: this module is imported both outside
and inside the realm.

Outcome vocabulary (exactly one per probe execution):

    DENIED        the attempted effect did not occur, for a reason that
                  is a genuine denial of that effect
    ALLOWED       the attempted effect occurred
    ERROR         the probe failed for a reason unrelated to the
                  effect's availability (never counted as denial)
    INCONCLUSIVE  the precondition for attempting the effect was absent

verdict = PASS iff observed_outcome == expected_outcome.
"""

from __future__ import annotations

POLICY_ID = ("realm/v2:unshare-mn+ro-nosuid-nodev-binds+chroot+"
             "setpriv-65534+no-new-privs+empty-caps")

# --- Obligation 1: privilege contract, measured in-realm ------------------

PRIVILEGE_CONTRACT = {
    "NoNewPrivs": "1",
    "CapInh": "0000000000000000",
    "CapPrm": "0000000000000000",
    "CapEff": "0000000000000000",
    "CapBnd": "0000000000000000",
    "CapAmb": "0000000000000000",
    "uid": "65534",
    "gid": "65534",
}

PRIVILEGE_CLAIM_SCOPE = (
    "Privilege monotonicity within the declared lattice: uid/gid, "
    "no_new_privs, and the five capability sets, under ro,nosuid,nodev "
    "bind mounts. NOT claimed: kernel-exploit resistance, side-channel "
    "isolation, VM-grade isolation."
)

# --- Obligation 2: typed probe declarations -------------------------------
# expected_outcome is the ONLY outcome that yields verdict PASS.

PROBES = (
    # Containment of the parent repository.
    {"probe_id": "parent_repo_visibility",
     "attempted_effect": "resolve any known parent-repository path",
     "expected_outcome": "DENIED",
     "note": "positive test: a visible parent yields ALLOWED and FAILS"},
    {"probe_id": "write_parent_worktree_file",
     "attempted_effect": "create a file inside the parent worktree",
     "expected_outcome": "DENIED"},
    {"probe_id": "write_parent_ref",
     "attempted_effect": "create a ref file under parent .git/refs/heads",
     "expected_outcome": "DENIED"},
    {"probe_id": "write_parent_git_config",
     "attempted_effect": "append to parent .git/config",
     "expected_outcome": "DENIED"},
    {"probe_id": "write_parent_git_object",
     "attempted_effect": "create a file under parent .git/objects",
     "expected_outcome": "DENIED"},
    # Host filesystem containment.
    {"probe_id": "write_ro_usr",
     "attempted_effect": "create a file under /usr",
     "expected_outcome": "DENIED"},
    {"probe_id": "write_ro_etc",
     "attempted_effect": "create a file under /etc",
     "expected_outcome": "DENIED"},
    {"probe_id": "write_realm_root",
     "attempted_effect": "create a file at the realm root",
     "expected_outcome": "DENIED"},
    # Credentials and communication.
    {"probe_id": "forbidden_env_present",
     "attempted_effect": "read credential/proxy environment variables",
     "expected_outcome": "DENIED",
     "note": "positive test over os.environ, not exception-based"},
    {"probe_id": "network_connect",
     "attempted_effect": "open an outbound TCP/HTTPS connection",
     "expected_outcome": "DENIED"},
    # Privilege escalation (Obligation 1 adversarial surface).
    {"probe_id": "setuid_root_syscall",
     "attempted_effect": "call setuid(0)",
     "expected_outcome": "DENIED"},
    {"probe_id": "setuid_binary_elevation",
     "attempted_effect": "exec a reachable setuid binary and gain euid 0",
     "expected_outcome": "DENIED"},
    {"probe_id": "mount_from_realm",
     "attempted_effect": "mount a filesystem from inside the realm",
     "expected_outcome": "DENIED"},
    {"probe_id": "unshare_from_realm",
     "attempted_effect": "create a new mount namespace from inside",
     "expected_outcome": "DENIED"},
    {"probe_id": "signal_host_process",
     "attempted_effect": "signal an out-of-realm process (pid 1)",
     "expected_outcome": "DENIED"},
    # Positive control: the surface must not be inert.
    {"probe_id": "write_scratch",
     "attempted_effect": "create a file in the writable scratch",
     "expected_outcome": "ALLOWED",
     "note": "control: a realm that denies everything proves nothing"},
)

PROBE_IDS = tuple(p["probe_id"] for p in PROBES)
EXPECTED_OUTCOME = {p["probe_id"]: p["expected_outcome"] for p in PROBES}

FORBIDDEN_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "HTTPS_PROXY", "HTTP_PROXY",
                 "AWS_SECRET_ACCESS_KEY", "ANTHROPIC_API_KEY",
                 "GIT_ASKPASS", "SSH_AUTH_SOCK")

PARENT_PATH_CANDIDATES = ("/home/user/genesis", "/parent", "/canonical")

SETUID_CANDIDATES = ("/usr/bin/su", "/bin/su", "/usr/bin/sudo",
                     "/usr/bin/mount", "/bin/mount", "/usr/bin/passwd",
                     "/usr/bin/newgrp", "/usr/bin/chsh")

# --- Obligation 3: integrity rulers, scope and metric ---------------------

INTEGRITY_RULERS = {
    "parent_tracked_worktree_digest": {
        "scope": "every path reported by `git ls-files -s` in the parent "
                 "repository working tree",
        "metric": "SHA-256 over sorted '<mode> <sha256(file bytes)> "
                  "<path>' lines; files are read, never written",
        "detects": "uncommitted content changes, mode changes, deletion "
                   "of tracked files",
        "ignores": "untracked files, ignored paths, timestamps, .git "
                   "internals (covered by the other rulers)",
    },
    "parent_object_store_digest": {
        "scope": "every regular file under the parent .git/objects "
                 "(loose objects, packs, pack indexes)",
        "metric": "SHA-256 over sorted '<sha256(file bytes)> <relpath>' "
                  "lines",
        "detects": "content mutation of existing objects at equal object "
                   "count, object addition, object removal",
        "ignores": "mtimes; object stores outside .git/objects",
    },
    "parent_refs_digest": {
        "scope": "all refs reported by `git for-each-ref` in the parent",
        "metric": "SHA-256 over sorted '<refname> <objectname>' lines",
        "detects": "ref creation, deletion, or retargeting",
        "ignores": "reflogs",
    },
}

RULER_IDS = tuple(INTEGRITY_RULERS)


def certify_privilege(measured: dict) -> tuple[bool, list[str]]:
    """Certify a measured privilege state against the frozen contract."""
    problems = []
    for key, want in PRIVILEGE_CONTRACT.items():
        got = str(measured.get(key, "MISSING"))
        if got != want:
            problems.append(f"{key}={got} (contract {want})")
    return (not problems), problems


def certify_probes(results: dict) -> tuple[bool, list[str]]:
    """Certify typed probe results. PASS requires every declared probe to
    be present with observed_outcome equal to its expected_outcome; an
    ERROR or INCONCLUSIVE outcome NEVER certifies."""
    problems = []
    for pid in PROBE_IDS:
        entry = results.get(pid)
        if not isinstance(entry, dict):
            problems.append(f"{pid}: missing result")
            continue
        observed = entry.get("observed_outcome")
        expected = EXPECTED_OUTCOME[pid]
        if observed != expected:
            problems.append(f"{pid}: observed {observed} != expected "
                            f"{expected}")
        if entry.get("verdict") != "PASS":
            problems.append(f"{pid}: verdict {entry.get('verdict')}")
    return (not problems), problems
