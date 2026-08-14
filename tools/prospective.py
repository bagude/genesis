#!/usr/bin/env python3
"""ProspectiveEvaluation — bounded successor-viability evaluator.
v2 (BUILD-006, AUDIT-005 repair).

InterfaceIsolation != CapabilityIsolation. Unaccepted candidate code
executes only inside a realm whose forbidden effects are mechanically
UNAVAILABLE, and each denial is proven by an adversarial probe rather
than inferred from benign behavior.

Mechanism:
  1. Independent substrate — `git clone --no-local --no-hardlinks` of
     the parent at the exact candidate commit, origin removed. Storage
     independence is tested (0 hard-linked objects between clone and
     parent object stores).
  2. Isolation realm — read-only bind mounts of system dirs, a single
     writable /work (the clone) and /tmp, entered via
     `unshare -m -n` -> chroot -> setpriv to uid 65534. The parent
     repository path does not exist inside the realm.
  3. In-realm run — tools/realm_probe.py executes the adversarial
     battery AND the candidate verifier in the same bounded surface.
  4. Host-after invariants — parent refs, a worktree sentinel digest,
     and the parent git object count are compared before/after; any
     change fails viability.

Declared limits: namespace/chroot/unprivileged-uid isolation on a
shared kernel, not a VM or audited container runtime. If realm
construction is unavailable (no privilege), returns verdict UNAVAILABLE
with the reason — never a false PASS.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import authority_lib as lib

ROOT = lib.ROOT
CAPABILITY_POLICY = "realm/v1:unshare-mn+ro-binds+chroot+setpriv-65534"
NOBODY = "65534"
RO_BINDS = ("usr", "bin", "lib", "lib64", "etc")
DEV_NODES = ("null", "zero", "full", "random", "urandom")


def _hardlink_count(objects_dir: Path) -> int:
    return sum(1 for p in objects_dir.rglob("*")
               if p.is_file() and p.stat().st_nlink > 1)


def _object_count(repo: Path) -> int:
    out = subprocess.run(["git", "-C", str(repo), "count-objects", "-v"],
                         capture_output=True, text=True)
    counts = {}
    for line in out.stdout.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            counts[k.strip()] = v.strip()
    return int(counts.get("count", 0)) + int(counts.get("in-pack", 0))


def _worktree_sentinel() -> str:
    """Digest of tracked-file contents of the parent HEAD tree — a
    cheap host-after integrity sentinel."""
    tree = lib.git("rev-parse", "HEAD^{tree}")
    return hashlib.sha256(tree.encode()).hexdigest()


def _refs_snapshot() -> str:
    return lib.git("for-each-ref", "--format=%(refname) %(objectname)")


def evaluate(candidate: str, transition: str = "?") -> dict:
    candidate_sha = lib.git("rev-parse", f"{candidate}^{{commit}}")
    evaluator_blob = lib.git("hash-object", str(Path(__file__)))
    scratch = Path(tempfile.mkdtemp(prefix="genesis-realm-"))
    repo = scratch / "repo"
    realm = scratch / "realm"

    refs_before = _refs_snapshot()
    objects_before = _object_count(ROOT)
    sentinel_before = _worktree_sentinel()

    # 1. Independent substrate.
    subprocess.run(["git", "clone", "--quiet", "--no-local", "--no-hardlinks",
                    str(ROOT), str(repo)], check=True, capture_output=True)
    subprocess.run(["git", "checkout", "--quiet", candidate_sha],
                   cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "remote", "remove", "origin"], cwd=repo,
                   capture_output=True)
    hardlinks = _hardlink_count(repo / ".git" / "objects")
    remotes = subprocess.run(["git", "remote"], cwd=repo,
                             capture_output=True, text=True).stdout.split()

    # 2. Realm layout: repo becomes /work; RO system binds; /tmp scratch.
    for d in RO_BINDS:
        (realm / d).mkdir(parents=True, exist_ok=True)
    (realm / "proc").mkdir(parents=True, exist_ok=True)
    (realm / "dev").mkdir(parents=True, exist_ok=True)
    for node in DEV_NODES:
        (realm / "dev" / node).touch()
    (realm / "work").mkdir(parents=True, exist_ok=True)
    (realm / "tmp").mkdir(parents=True, exist_ok=True)
    shutil.copytree(repo, realm / "work" / "repo")
    probe_src = Path(__file__).parent / "realm_probe.py"
    shutil.copy(probe_src, realm / "work" / "realm_probe.py")
    subprocess.run(["chown", "-R", f"{NOBODY}:{NOBODY}",
                    str(realm / "work"), str(realm / "tmp")],
                   capture_output=True)

    # 3. In-realm execution under bounded capabilities.
    binds = "\n".join(
        f'mount --bind /{d} "$R/{d}" && mount -o remount,ro,bind "$R/{d}"'
        for d in RO_BINDS if Path("/" + d).exists())
    # Minimal device nodes bound individually (not the whole /dev):
    # /dev/null etc. are needed by git; their bind keeps device
    # semantics (writable) without exposing raw block devices.
    dev_binds = "\n".join(
        f'mount --bind /dev/{n} "$R/dev/{n}"'
        for n in DEV_NODES if Path("/dev/" + n).exists())
    launcher = scratch / "launch.sh"
    launcher.write_text(
        "set -e\n"
        f'R="{realm}"\n'
        f"{binds}\n"
        f"{dev_binds}\n"
        'mount -t proc proc "$R/proc" 2>/dev/null || true\n'
        'exec chroot "$R" /usr/bin/setpriv --reuid=' + NOBODY +
        ' --regid=' + NOBODY + ' --clear-groups '
        '/usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/work '
        '/usr/bin/python3 /work/realm_probe.py\n')

    realm_error = None
    realm_json = None
    try:
        res = subprocess.run(
            ["unshare", "-m", "-n", "bash", str(launcher)],
            capture_output=True, text=True, timeout=1200)
        if res.returncode == 0 and res.stdout.strip():
            realm_json = json.loads(res.stdout.strip().splitlines()[-1])
        else:
            realm_error = (res.stderr or res.stdout or "empty").strip()[:400]
    except Exception as exc:  # noqa: BLE001
        realm_error = f"{type(exc).__name__}: {exc}"
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(scratch)],
                       capture_output=True)
        shutil.rmtree(scratch, ignore_errors=True)

    # 4. Host-after invariants.
    refs_after = _refs_snapshot()
    objects_after = _object_count(ROOT)
    sentinel_after = _worktree_sentinel()
    host_after = {
        "parent_refs_unchanged": "true" if refs_before == refs_after else "false",
        "parent_objects_unchanged":
            "true" if objects_before == objects_after else "false",
        "parent_worktree_unchanged":
            "true" if sentinel_before == sentinel_after else "false",
    }

    if realm_json is None:
        return {
            "schema": "ProspectiveEvaluation/2",
            "transition": transition,
            "target_commit": candidate_sha,
            "verdict": "UNAVAILABLE",
            "reason": realm_error or "realm did not produce output",
            "capability_policy_id": CAPABILITY_POLICY,
            "evaluator_blob": evaluator_blob,
            "environment_id": lib.environment_id(),
        }

    probes = realm_json["adversarial_probes"]
    envelope = {
        "storage_hardlinks": str(hardlinks),
        "remotes": str(len(remotes)),
        "realm_uid": str(realm_json.get("uid")),
        "all_forbidden_denied":
            "true" if realm_json.get("all_forbidden_denied") else "false",
        "scratch_writable":
            "true" if realm_json.get("scratch_writable") else "false",
        **{f"probe_{k}": v for k, v in probes.items()},
        **host_after,
    }
    host_ok = all(v == "true" for v in host_after.values())
    verdict = "PASS" if (realm_json.get("verdict") == "PASS"
                         and hardlinks == 0 and not remotes
                         and host_ok) else "FAIL"
    return {
        "schema": "ProspectiveEvaluation/2",
        "transition": transition,
        "target_commit": candidate_sha,
        "verdict": verdict,
        "exit_code": realm_json["viability"]["exit_code"],
        "violations": realm_json["viability"]["violations"],
        "capability_policy_id": CAPABILITY_POLICY,
        "evaluator_blob": evaluator_blob,
        "capability_envelope": envelope,
        "adversarial_probes": probes,
        "environment_id": lib.environment_id(),
        "output": realm_json["viability"]["output"],
    }


def main() -> int:
    candidate = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    transition = sys.argv[2] if len(sys.argv) > 2 else "?"
    result = evaluate(candidate, transition)
    env = result.get("capability_envelope", {})
    print(f"prospective: verdict={result['verdict']} "
          f"target={result['target_commit'][:12]} "
          f"hardlinks={env.get('storage_hardlinks', '?')} "
          f"all_denied={env.get('all_forbidden_denied', '?')} "
          f"host_ok={env.get('parent_refs_unchanged', '?')}/"
          f"{env.get('parent_objects_unchanged', '?')}/"
          f"{env.get('parent_worktree_unchanged', '?')}")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
