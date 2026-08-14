#!/usr/bin/env python3
"""ProspectiveEvaluation — bounded successor evaluator.
v3 (BUILD-007, AUDIT-006 repair).

Evaluates a target commit — the candidate payload OR the staged
would-be accepted state — inside a realm whose privilege surface is
frozen and whose denials are typed:

  1. Independent substrate: `git clone --no-local --no-hardlinks` at the
     exact target commit, origin removed (0 hard-linked objects).
  2. Realm: `unshare -m -n` -> ro,nosuid,nodev binds of system dirs ->
     minimal /dev -> chroot -> `setpriv --reuid/--regid --clear-groups
     --no-new-privs --bounding-set=-all --inh-caps=-all
     --ambient-caps=-all`. Privilege monotonicity is MEASURED inside
     the realm from /proc/self/status, not assumed from these flags.
  3. Typed adversarial probes (tools/realm_probe.py + the frozen
     tools/capability_policy.py) — effect semantics, never exception
     semantics.
  4. Integrity rulers with declared SCOPE and METRIC computed on the
     parent before and after: tracked-worktree content digest, object
     store content digest, refs digest. The certificate asserts
     IntegrityBefore(Scope) = IntegrityAfter(Scope) — never an
     unqualified "unchanged".

Declared claim scope is capability_policy.PRIVILEGE_CLAIM_SCOPE. If the
realm cannot be constructed (no privilege), the verdict is UNAVAILABLE
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
import capability_policy as pol

ROOT = lib.ROOT
NOBODY = "65534"
RO_BINDS = ("usr", "bin", "lib", "lib64", "etc")
DEV_NODES = ("null", "zero", "full", "random", "urandom")


# --- Obligation 3: integrity rulers (read-only; scope per policy) ---------

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked_worktree_digest() -> str:
    """SCOPE: every `git ls-files -s` path. METRIC: SHA-256 over sorted
    '<mode> <sha256(bytes)> <path>' lines. Reads only."""
    lines = []
    for entry in lib.git("ls-files", "-s").splitlines():
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        mode = meta.split()[0]
        f = ROOT / path
        try:
            digest = _sha256_file(f) if f.is_file() else "MISSING"
        except OSError as exc:
            digest = f"UNREADABLE:{exc.errno}"
        lines.append(f"{mode} {digest} {path}")
    body = "\n".join(sorted(lines)) + "\n"
    return hashlib.sha256(body.encode()).hexdigest()


def object_store_digest() -> str:
    """SCOPE: every regular file under .git/objects. METRIC: SHA-256 over
    sorted '<sha256(bytes)> <relpath>' lines. Reads only."""
    objects = ROOT / ".git" / "objects"
    lines = []
    if objects.is_dir():
        for f in sorted(objects.rglob("*")):
            if not f.is_file():
                continue
            try:
                lines.append(f"{_sha256_file(f)} "
                             f"{f.relative_to(objects).as_posix()}")
            except OSError as exc:
                lines.append(f"UNREADABLE:{exc.errno} "
                             f"{f.relative_to(objects).as_posix()}")
    body = "\n".join(sorted(lines)) + "\n"
    return hashlib.sha256(body.encode()).hexdigest()


def refs_digest() -> str:
    """SCOPE: all refs. METRIC: SHA-256 over sorted refname/objectname."""
    body = "\n".join(sorted(
        lib.git("for-each-ref", "--format=%(refname) %(objectname)")
        .splitlines())) + "\n"
    return hashlib.sha256(body.encode()).hexdigest()


def measure_integrity() -> dict:
    return {
        "parent_tracked_worktree_digest": tracked_worktree_digest(),
        "parent_object_store_digest": object_store_digest(),
        "parent_refs_digest": refs_digest(),
    }


def _hardlink_count(objects_dir: Path) -> int:
    return sum(1 for p in objects_dir.rglob("*")
               if p.is_file() and p.stat().st_nlink > 1)


# --- realm construction and evaluation -----------------------------------

def evaluate(target: str, transition: str = "?",
             stage: str = "payload") -> dict:
    """Evaluate `target` (a commit) in the realm. `stage` is
    'payload' (candidate) or 'canonical' (staged accepted state); it is
    recorded in the evidence so the two viability surfaces never
    collapse into one claim."""
    target_sha = lib.git("rev-parse", f"{target}^{{commit}}")
    evaluator_blob = lib.git("hash-object", str(Path(__file__)))
    policy_blob = lib.git("hash-object",
                          str(Path(__file__).parent / "capability_policy.py"))
    scratch = Path(tempfile.mkdtemp(prefix="genesis-realm-"))
    repo = scratch / "repo"
    realm = scratch / "realm"

    integrity_before = measure_integrity()

    subprocess.run(["git", "clone", "--quiet", "--no-local", "--no-hardlinks",
                    str(ROOT), str(repo)], check=True, capture_output=True)
    subprocess.run(["git", "checkout", "--quiet", target_sha],
                   cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "remote", "remove", "origin"], cwd=repo,
                   capture_output=True)
    hardlinks = _hardlink_count(repo / ".git" / "objects")
    remotes = subprocess.run(["git", "remote"], cwd=repo,
                             capture_output=True, text=True).stdout.split()

    for d in RO_BINDS:
        (realm / d).mkdir(parents=True, exist_ok=True)
    (realm / "proc").mkdir(parents=True, exist_ok=True)
    (realm / "dev").mkdir(parents=True, exist_ok=True)
    for node in DEV_NODES:
        (realm / "dev" / node).touch()
    (realm / "work").mkdir(parents=True, exist_ok=True)
    (realm / "tmp").mkdir(parents=True, exist_ok=True)
    shutil.copytree(repo, realm / "work" / "repo")
    here = Path(__file__).parent
    for helper in ("realm_probe.py", "capability_policy.py"):
        shutil.copy(here / helper, realm / "work" / helper)
    subprocess.run(["chown", "-R", f"{NOBODY}:{NOBODY}",
                    str(realm / "work"), str(realm / "tmp")],
                   capture_output=True)

    # ro,nosuid,nodev: no setuid/file-capability path through host mounts.
    binds = "\n".join(
        f'mount --bind /{d} "$R/{d}" && '
        f'mount -o remount,ro,nosuid,nodev,bind "$R/{d}"'
        for d in RO_BINDS if Path("/" + d).exists())
    dev_binds = "\n".join(f'mount --bind /dev/{n} "$R/dev/{n}"'
                          for n in DEV_NODES if Path("/dev/" + n).exists())
    launcher = scratch / "launch.sh"
    launcher.write_text(
        "set -e\n"
        f'R="{realm}"\n'
        f"{binds}\n"
        f"{dev_binds}\n"
        'mount -t proc proc "$R/proc" 2>/dev/null || true\n'
        'exec chroot "$R" /usr/bin/setpriv '
        f'--reuid={NOBODY} --regid={NOBODY} --clear-groups '
        '--no-new-privs --bounding-set=-all --inh-caps=-all '
        '--ambient-caps=-all '
        '/usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/work '
        '/usr/bin/python3 /work/realm_probe.py\n')

    realm_error = None
    realm_json = None
    try:
        res = subprocess.run(["unshare", "-m", "-n", "bash", str(launcher)],
                             capture_output=True, text=True, timeout=1800)
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

    integrity_after = measure_integrity()
    integrity = {
        f"{name}_equal":
            "true" if integrity_before[name] == integrity_after[name] else "false"
        for name in pol.RULER_IDS
    }
    integrity_ok = all(v == "true" for v in integrity.values())

    base = {
        "schema": "ProspectiveEvaluation/3",
        "transition": transition,
        "stage": stage,
        "target_commit": target_sha,
        "capability_policy_id": pol.POLICY_ID,
        "capability_policy_blob": policy_blob,
        "evaluator_blob": evaluator_blob,
        "environment_id": lib.environment_id(),
        "integrity_before": integrity_before,
        "integrity_after": integrity_after,
    }
    if realm_json is None:
        base.update({"verdict": "UNAVAILABLE",
                     "reason": realm_error or "realm produced no output"})
        return base

    probes_ok, probe_problems = pol.certify_probes(realm_json["probes"])
    priv_ok, priv_problems = pol.certify_privilege(
        realm_json["privilege_measured"])
    verifier_ok = (realm_json["viability"]["exit_code"] == 0
                   and not realm_json["viability"]["violations"])
    verdict = "PASS" if (probes_ok and priv_ok and verifier_ok
                         and integrity_ok and hardlinks == 0
                         and not remotes) else "FAIL"
    base.update({
        "verdict": verdict,
        "exit_code": realm_json["viability"]["exit_code"],
        "violations": realm_json["viability"]["violations"],
        "privilege_measured": realm_json["privilege_measured"],
        "privilege_certified": priv_ok,
        "privilege_problems": priv_problems,
        "probes": realm_json["probes"],
        "probes_certified": probes_ok,
        "probe_problems": probe_problems,
        "capability_envelope": {
            "storage_hardlinks": str(hardlinks),
            "remotes": str(len(remotes)),
            "no_new_privs": realm_json["privilege_measured"].get("NoNewPrivs"),
            "realm_uid": realm_json["privilege_measured"].get("uid"),
            **integrity,
            **{f"probe_{k}": v["observed_outcome"]
               for k, v in realm_json["probes"].items()},
        },
        "output": realm_json["viability"]["output"],
    })
    return base


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    transition = sys.argv[2] if len(sys.argv) > 2 else "?"
    stage = sys.argv[3] if len(sys.argv) > 3 else "payload"
    r = evaluate(target, transition, stage)
    env = r.get("capability_envelope", {})
    print(f"prospective[{stage}]: verdict={r['verdict']} "
          f"target={r['target_commit'][:12]} "
          f"privilege_certified={r.get('privilege_certified')} "
          f"probes_certified={r.get('probes_certified')} "
          f"nnp={env.get('no_new_privs')} "
          f"hardlinks={env.get('storage_hardlinks')}")
    if r.get("probe_problems"):
        print("  probe problems:", r["probe_problems"])
    if r.get("privilege_problems"):
        print("  privilege problems:", r["privilege_problems"])
    return 0 if r["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
