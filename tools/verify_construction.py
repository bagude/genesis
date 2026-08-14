#!/usr/bin/env python3
"""Construction-ledger verifier (law for construction/ records).

v3 (BUILD-002, AUDIT-001 repair). The verifier is split into two
operators with distinct capability sets:

  R_B — passive measurement: derivation over git evidence only. No
        command execution, no writes. K_RB^write = 0.
  E_B — active experiment: probes resolved exclusively through the
        law-controlled registry tools/probes.yaml (proposals reference
        probes by name; proposal data can never inject a command),
        executed in an ephemeral detached git worktree so the
        authoritative tree is never the experiment's substrate.
        Isolation is attested by tree-status snapshot equality.

Governance closure added over v2:

  * Attribution freeze — a grounded transition's attribution is frozen
    at the commit adding its grounding; later commits reusing its
    trailer are violations (attribution_extensions).
  * Record immutability — construction/{proposals,groundings,audits}/
    are add-only over all history (closed_record_mutations); proposal
    commits may contain additions only.
  * Canonical evidence identity — from BUILD-002 onward,
    evidence.proposal_commit must equal the full 40-hex derived commit
    id exactly (BUILD-001's prefix relation is grandfathered as a
    closed record).

Carried over from v2 (BUILD-001): trailer attribution with legacy
grandfather clause, precedence via strict ancestry, scope via
realization-diff union, budget via transition file count, format-2
groundings restricted to derived-or-reported_ keys, open-proposal
lifecycle, untracked-commit law.

Exit code 0 means the construction ledger is law-conformant.
Stdlib + pyyaml only, by declaration of BUILD-000/001/002.
"""

from __future__ import annotations

import hashlib
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import authority_lib as lib  # noqa: E402  (single source of authority truth)

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "construction" / "schemas"
PROPOSALS = ROOT / "construction" / "proposals"
GROUNDINGS = ROOT / "construction" / "groundings"
RECEIPTS = ROOT / "construction" / "receipts"
REGISTRY = ROOT / "tools" / "probes.yaml"

RECORD_NAMESPACES = ("construction/proposals/", "construction/groundings/",
                     "construction/audits/", "construction/receipts/",
                     "construction/rejections/", "construction/evidence/")
IMPLICIT_SCOPE = ("construction/proposals/", "construction/groundings/",
                  "construction/audits/")
RECEIPT_COMMIT_SCOPE = ("construction/receipts/", "construction/rejections/",
                        "construction/evidence/")
PROPOSAL_COMMIT_SCOPE = ("construction/proposals/", "construction/audits/")
TRAILER_RE = re.compile(r"^Construction-Transition:\s*(BUILD-\d{3})\s*$",
                        re.MULTILINE)
RECEIPT_RE = re.compile(r"^Construction-Receipt:\s*(BUILD-\d{3})\s*$",
                        re.MULTILINE)
FORMAT2_FROM = 1        # first proposal whose grounding must be format 2
CANONICAL_ID_FROM = 2   # first proposal requiring full-SHA evidence identity
REGISTRY_ONLY_FROM = 2  # first proposal whose probes are names, not specs
RECEIPT_BOUND_FROM = 3  # first proposal whose receipt (if present) is
                        # closure-binding for gate verdicts and probes;
                        # BUILD-003 is the declared bootstrap
RECEIPT_REQUIRED_FROM = 4  # first proposal whose closed grounding MUST
                           # have a promotion receipt

FAILURES: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)


def git(*args: str) -> str:
    res = subprocess.run(["git", *args], capture_output=True, text=True,
                         cwd=ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {res.stderr.strip()}")
    return res.stdout.strip()


def load_yaml(path: Path) -> dict:
    with path.open() as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)}: top level is not a mapping")
        return {}
    return data


def type_ok(value: object, decl: str) -> bool:
    if decl == "str":
        return isinstance(value, str)
    if decl == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if decl == "map":
        return isinstance(value, dict)
    if decl == "map[str]":
        return isinstance(value, dict) and all(
            isinstance(k, str) and isinstance(v, str) for k, v in value.items()
        )
    if decl == "list[str]":
        return isinstance(value, list) and all(isinstance(x, str) for x in value)
    if decl == "list":
        return isinstance(value, list)
    raise ValueError(f"unknown type declaration in schema: {decl}")


def check_required(record: dict, spec: dict, label: str) -> None:
    for key, decl in spec.items():
        if key not in record:
            fail(f"{label}: missing required key '{key}'")
        elif not type_ok(record[key], decl):
            fail(f"{label}: key '{key}' is not of type {decl}")


def pid_number(pid: str) -> int:
    return int(pid.split("-")[1])


# --- repository evidence (R_B: read-only) ----------------------------------

def all_commits() -> list[str]:
    out = git("log", "--format=%H")
    return out.split("\n") if out else []


def commit_files(sha: str) -> list[str]:
    out = git("show", "--name-only", "--format=", sha)
    return [line for line in out.split("\n") if line]


def commit_name_status(sha: str) -> list[tuple[str, str]]:
    out = git("show", "--name-status", "--format=", sha)
    entries = []
    for line in out.split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        entries.append((parts[0], parts[-1]))
    return entries


def commit_trailer(sha: str) -> str | None:
    body = git("show", "-s", "--format=%B", sha)
    match = TRAILER_RE.search(body)
    return match.group(1) if match else None


def receipt_trailer(sha: str) -> str | None:
    body = git("show", "-s", "--format=%B", sha)
    match = RECEIPT_RE.search(body)
    return match.group(1) if match else None


def adding_commit(relpath: str) -> str | None:
    out = git("log", "--diff-filter=A", "--format=%H", "--", relpath)
    lines = [line for line in out.split("\n") if line]
    return lines[-1] if lines else None  # oldest


def is_strict_ancestor(a: str, b: str) -> bool:
    if a == b:
        return False
    res = subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                         capture_output=True, cwd=ROOT)
    return res.returncode == 0


def is_ancestor_or_equal(a: str, b: str) -> bool:
    return a == b or is_strict_ancestor(a, b)


def attribute_commits(pids: list[str]) -> dict[str, set[str]]:
    """Map proposal id -> set of commit shas belonging to its transition."""
    attribution: dict[str, set[str]] = {pid: set() for pid in pids}
    for sha in all_commits():
        pid = commit_trailer(sha)
        if pid is not None:
            if pid in attribution:
                attribution[pid].add(sha)
            else:
                fail(f"commit {sha[:7]}: trailer references unknown "
                     f"proposal '{pid}'")
    # Grandfather clause: legacy commits are attributed by record files.
    for pid in pids:
        for rel in (f"construction/proposals/{pid}.yaml",
                    f"construction/groundings/{pid}.yaml"):
            out = git("log", "--format=%H", "--", rel)
            for sha in [line for line in out.split("\n") if line]:
                attribution[pid].add(sha)
    return attribution


# --- experiments (E_B: registry-resolved, isolated) -------------------------

def environment_id() -> str:
    """Delegates to authority_lib — one derivation everywhere
    (AUDIT-003: never two implementations of an identity rule)."""
    return lib.environment_id()


# BUILD-003 bootstrap identity discrepancy (AUDIT-003 Finding 1).
# These are FROZEN HISTORICAL constants from PRE-AUDIT-003-BOOTSTRAP;
# the derived value is recomputed mechanically on every run so the
# discrepancy stays permanently visible and is never silently
# normalized. Closed records are not mutated.
B003_BOOTSTRAP_MEMBERS = [
    ("c495d9ffaa7e89f6b210de8672b4a034f3227bbb", "tools/verify_construction.py"),
    ("01eb084c0d6b856d5b80da368abad96d2cf7e57b", "tools/probes.yaml"),
    ("a706e30ba7dae9bd17b6114144bbe3d2a123d870", "construction/schemas/build_proposal.schema.yaml"),
    ("dcadfd1efa6a3981883b570a876c58662ef74ddc", "construction/schemas/build_grounding.schema.yaml"),
]
B003_RECORDED_IDENTITY = \
    "a498931e482a1022e03f80f3291d75f28177363e5f65ee05d42a1a10a69ad4ac"


def b003_bootstrap_discrepancy() -> dict[str, str]:
    lines = sorted(f"{b} {p}" for b, p in B003_BOOTSTRAP_MEMBERS)
    derived = hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()
    status = "MATCH" if derived == B003_RECORDED_IDENTITY \
        else "MISMATCH_ARCHIVED_AUDIT-003"
    return {
        "bootstrap_identity_recorded_BUILD-003": B003_RECORDED_IDENTITY,
        "bootstrap_identity_derived_BUILD-003": derived,
        "bootstrap_identity_status_BUILD-003": status,
    }


def load_registry() -> dict[str, dict]:
    if not REGISTRY.exists():
        return {}
    data = load_yaml(REGISTRY)
    probes = data.get("probes")
    return probes if isinstance(probes, dict) else {}


def resolve_probes(pid: str, declared: list, registry: dict[str, dict]) -> list[str]:
    """Return registry probe names for a proposal; violations for anything
    that would let proposal data control execution."""
    names: list[str] = []
    for entry in declared or []:
        if isinstance(entry, str):
            name, legacy = entry, None
        elif isinstance(entry, dict):
            if pid_number(pid) >= REGISTRY_ONLY_FROM:
                fail(f"{pid}: inline probe specs are unlawful from "
                     f"BUILD-{REGISTRY_ONLY_FROM:03d}; reference registry "
                     f"probes by name")
                continue
            name, legacy = entry.get("name"), entry
        else:
            fail(f"{pid}: malformed probe entry {entry!r}")
            continue
        if not isinstance(name, str) or name not in registry:
            fail(f"{pid}: probe '{name}' is not in the registry")
            continue
        if legacy is not None:
            reg = registry[name]
            if (legacy.get("cmd") != reg.get("cmd")
                    or legacy.get("expect_exit", 0) != reg.get("expect_exit", 0)):
                fail(f"{pid}: legacy inline probe '{name}' disagrees with "
                     f"the registry definition")
                continue
        names.append(name)
    return names


def run_experiments(probe_names: set[str],
                    registry: dict[str, dict]) -> dict[str, str]:
    """Execute registry probes in an ephemeral detached worktree. Returns
    derived probe_<name> results plus experiment_tree_isolation."""
    results: dict[str, str] = {}
    if not probe_names:
        return results
    before = git("status", "--porcelain")
    scratch = Path(tempfile.mkdtemp(prefix="genesis-experiment-"))
    worktree = scratch / "tree"
    try:
        git("worktree", "add", "--detach", str(worktree), "HEAD")
        for name in sorted(probe_names):
            reg = registry[name]
            cmd, expect = reg.get("cmd"), reg.get("expect_exit", 0)
            if not isinstance(cmd, str):
                fail(f"registry probe '{name}' has no command")
                results[f"probe_{name}"] = "FAIL"
                continue
            try:
                res = subprocess.run(cmd, shell=True, capture_output=True,
                                     cwd=worktree, timeout=300)
                outcome = "PASS" if res.returncode == expect else "FAIL"
            except subprocess.TimeoutExpired:
                outcome = "FAIL"
            results[f"probe_{name}"] = outcome
            if outcome != "PASS":
                fail(f"probe '{name}' failed ({cmd})")
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree)],
                       capture_output=True, cwd=ROOT)
    after = git("status", "--porcelain")
    isolated = "PASS" if before == after else "FAIL"
    # Narrowed name (AUDIT-002 secondary finding): the measured invariant
    # is authoritative-tree STATUS preservation, nothing stronger. The
    # old key remains as a derived alias so closed records keep matching.
    results["authoritative_tree_status_preserved"] = isolated
    results["experiment_tree_isolation"] = isolated
    if isolated != "PASS":
        fail("experiment phase altered the authoritative tree status")
    return results


# --- derivation per transition (R_B) ----------------------------------------

def derive_transition(pid: str, proposal: dict, commits: set[str],
                      has_grounding: bool) -> dict[str, str]:
    derived: dict[str, str] = {}
    pcommit = adding_commit(f"construction/proposals/{pid}.yaml")
    if pcommit is None:
        fail(f"{pid}: proposal file has no adding commit in history")
        return derived
    derived[f"proposal_commit_{pid}"] = pcommit

    # Proposal-commit law: additions only, within record namespaces.
    for status, f in commit_name_status(pcommit):
        if not f.startswith(PROPOSAL_COMMIT_SCOPE):
            fail(f"{pid}: proposal commit {pcommit[:7]} touches non-proposal "
                 f"path {f}")
        if not status.startswith("A"):
            fail(f"{pid}: proposal commit {pcommit[:7]} performs '{status}' "
                 f"on {f}; proposal commits may only add records")

    realization = sorted(commits - {pcommit})

    if has_grounding:
        # Pre-proposal record commits are lawful inputs to a proposal
        # (AUDIT-003 protocol: archive audit -> freeze bootstrap ->
        # preregister), provided they touch ONLY the audit-record
        # namespace. Everything else attributed must strictly follow
        # the proposal commit. (Repairs the V_BUILD-003 defect archived
        # in BUILD-004-BOOTSTRAP.)
        pre = [c for c in realization if is_strict_ancestor(c, pcommit)]
        post = [c for c in realization if is_strict_ancestor(pcommit, c)]
        stray = sorted(set(realization) - set(pre) - set(post))
        bad_pre = [c for c in pre
                   if any(not f.startswith("construction/audits/")
                          for f in commit_files(c))]
        if not post:
            derived[f"proposal_precedence_{pid}"] = "FAIL"
            fail(f"{pid}: grounded but no realization commit follows the "
                 f"proposal commit")
        elif stray or bad_pre:
            derived[f"proposal_precedence_{pid}"] = "FAIL"
            for c in stray:
                fail(f"{pid}: attributed commit {c[:7]} is neither an "
                     f"ancestor nor a descendant of the proposal commit")
            for c in bad_pre:
                fail(f"{pid}: pre-proposal attributed commit {c[:7]} "
                     f"touches paths outside construction/audits/")
        else:
            derived[f"proposal_precedence_{pid}"] = "PASS"

    scope = tuple(proposal.get("allowed_scope", [])) + IMPLICIT_SCOPE
    realization_files: set[str] = set()
    for sha in realization:
        realization_files.update(commit_files(sha))
    out_of_scope = sorted(f for f in realization_files
                          if not f.startswith(scope))
    if has_grounding or realization:
        if out_of_scope:
            derived[f"scope_conformance_{pid}"] = "FAIL"
            fail(f"{pid}: files outside allowed_scope: {out_of_scope}")
        else:
            derived[f"scope_conformance_{pid}"] = "PASS"

    transition_files: set[str] = set(commit_files(pcommit)) | realization_files
    budget = proposal.get("budget", {})
    max_files = budget.get("max_files_changed")
    derived[f"files_changed_{pid}"] = str(len(transition_files))
    if isinstance(max_files, int) and (has_grounding or realization):
        if len(transition_files) <= max_files:
            derived[f"budget_conformance_{pid}"] = "PASS"
        else:
            derived[f"budget_conformance_{pid}"] = "FAIL"
            fail(f"{pid}: {len(transition_files)} files changed exceeds "
                 f"budget {max_files}")

    return derived


# --- global governance measurements (R_B, time-indexed) ---------------------
#
# Ledger-global keys are TIME-INDEXED: a closed grounding is validated
# against the ledger as of its own closure boundary, never against HEAD
# (otherwise every closed record would be invalidated the moment a new
# proposal opens). `boundary=None` means "now": HEAD history plus the
# working tree, used for laws and for a not-yet-committed grounding.

def commits_at(boundary: str | None) -> list[str]:
    out = git("log", "--format=%H", boundary) if boundary else \
        git("log", "--format=%H")
    return out.split("\n") if out else []


def record_stems_at(boundary: str | None, namespace: str,
                    live_dir: Path) -> set[str]:
    if boundary is None:
        return {p.stem for p in live_dir.glob("*.yaml")} if live_dir.exists() else set()
    out = git("ls-tree", "-r", "--name-only", boundary, "--", namespace)
    return {Path(f).stem for f in out.split("\n") if f}


def measure_globals(boundary: str | None, enforce: bool) -> dict[str, str]:
    """Derive ledger-global measurements as of `boundary` (None = now).
    Laws add FAILURES only when `enforce` is set (the present state)."""
    commits = commits_at(boundary)
    proposals_at = record_stems_at(boundary, "construction/proposals", PROPOSALS)
    grounded_at = record_stems_at(boundary, "construction/groundings", GROUNDINGS)

    # Lifecycle.
    open_ = sorted(proposals_at - grounded_at)
    if enforce:
        if len(open_) > 1:
            fail(f"lifecycle: more than one OPEN proposal: {open_}")
        if open_ and proposals_at:
            newest = max(proposals_at, key=pid_number)
            if open_[0] != newest:
                fail(f"lifecycle: OPEN proposal {open_[0]} is not the "
                     f"highest-numbered ({newest})")

    # Untracked commits beyond the measurement-law boundary. A commit is
    # tracked by a Construction-Transition trailer OR by a
    # Construction-Receipt trailer (the authorized post-promotion
    # append, restricted to the receipt namespaces, additions only).
    law_boundary = adding_commit("construction/groundings/BUILD-001.yaml")
    untracked = 0
    if law_boundary is not None and law_boundary in set(commits):
        for sha in commits:
            if sha == law_boundary or not is_strict_ancestor(law_boundary, sha):
                continue
            rcpt = receipt_trailer(sha)
            if rcpt is not None:
                for status, f in commit_name_status(sha):
                    if not status.startswith("A") or \
                            not f.startswith(RECEIPT_COMMIT_SCOPE):
                        if enforce:
                            fail(f"commit {sha[:7]}: receipt commit performs "
                                 f"'{status}' on {f}; receipt commits may "
                                 f"only add under {RECEIPT_COMMIT_SCOPE}")
                continue
            if commit_trailer(sha) is None:
                untracked += 1
                if enforce:
                    fail(f"commit {sha[:7]}: descends from measurement-law "
                         f"boundary but carries no Construction-Transition "
                         f"trailer")

    # Attribution freeze: Grounded(P_i) => Attribution(P_i) frozen.
    extensions = 0
    commit_set = set(commits)
    for pid in sorted(grounded_at):
        pid_boundary = adding_commit(f"construction/groundings/{pid}.yaml")
        if pid_boundary is None or pid_boundary not in commit_set:
            continue
        attributed: set[str] = set()
        for sha in commits:
            if commit_trailer(sha) == pid:
                attributed.add(sha)
        for rel in (f"construction/proposals/{pid}.yaml",
                    f"construction/groundings/{pid}.yaml"):
            out = git("log", "--format=%H", boundary or "HEAD", "--", rel)
            attributed.update(line for line in out.split("\n") if line)
        for sha in sorted(attributed):
            if not is_ancestor_or_equal(sha, pid_boundary):
                extensions += 1
                if enforce:
                    fail(f"{pid}: commit {sha[:7]} extends a closed "
                         f"transition (grounded at {pid_boundary[:7]})")

    # Record immutability: record namespaces are add-only.
    mutations = 0
    args = ["log", "--diff-filter=MDRT", "--name-status", "--format=%H"]
    if boundary:
        args.append(boundary)
    args += ["--", *[ns.rstrip("/") for ns in RECORD_NAMESPACES]]
    current = None
    for line in git(*args).split("\n"):
        if not line:
            continue
        if re.fullmatch(r"[0-9a-f]{40}", line):
            current = line
            continue
        parts = line.split("\t")
        status, path = parts[0], parts[-1]
        if path.startswith(RECORD_NAMESPACES):
            mutations += 1
            if enforce:
                fail(f"record immutability: commit "
                     f"{current[:7] if current else '?'} performs "
                     f"'{status}' on record {path}")
    return {
        "open_proposals": str(len(open_)),
        "untracked_commits": str(untracked),
        "attribution_extensions": str(extensions),
        "closed_record_mutations": str(mutations),
    }


# --- promotion receipts (G_B evidence, closure-bound) ------------------------

def check_receipts(proposals: dict[str, dict],
                   grounded: set[str]) -> tuple[dict[str, dict], dict[str, str]]:
    """Validate PromotionReceipts. Content checks (exact-target, PASS,
    authority present) apply to all; schema_version >= 2 receipts are
    additionally validated for PROVENANCE (AUDIT-003): the authority
    identity is recomputed from actual git objects at the receipt's
    parent canonical, and the bound GateResult evidence object must
    exist on the evidence ref and bind exactly this target, authority,
    environment, and verdict. Receipt contents alone never establish
    validity for v2 receipts.

    Gate-compatible requirement rule (repairs the V_BUILD-003 defect
    archived in BUILD-004-BOOTSTRAP): a closed transition >=
    RECEIPT_REQUIRED_FROM must have a receipt only once canonical
    history extends beyond its closure commit — a finalized,
    unpromoted candidate is not required to contain its own receipt."""
    receipts: dict[str, dict] = {}
    provenance: dict[str, str] = {}
    head = git("rev-parse", "HEAD")
    if RECEIPTS.exists():
        for path in sorted(RECEIPTS.glob("*.yaml")):
            pid = path.stem
            rec = load_yaml(path)
            label = str(path.relative_to(ROOT))
            if pid not in proposals:
                fail(f"{label}: receipt for unknown proposal '{pid}'")
                continue
            receipts[pid] = rec
            boundary = adding_commit(f"construction/groundings/{pid}.yaml")
            target = rec.get("target_commit")
            if boundary is not None and target != boundary:
                fail(f"{label}: target_commit '{target}' does not equal the "
                     f"transition's final commit '{boundary}' "
                     f"(exact-target invariant)")
            if rec.get("parent_law_verdict") != "PASS":
                fail(f"{label}: promoted receipt carries parent_law_verdict "
                     f"'{rec.get('parent_law_verdict')}'")
            if not rec.get("authority_identity"):
                fail(f"{label}: missing authority_identity")

            if rec.get("schema_version", 1) >= 2:
                provenance[pid] = check_receipt_provenance(label, rec)
            else:
                # BUILD-003-era receipt: content observable, provenance
                # not mechanically reconstructable (AUDIT-003). Never
                # silently normalized.
                provenance[pid] = "HISTORICAL_UNVERIFIED"
    for pid in sorted(grounded):
        if pid not in proposals or pid_number(pid) < RECEIPT_REQUIRED_FROM \
                or pid in receipts:
            continue
        boundary = adding_commit(f"construction/groundings/{pid}.yaml")
        if boundary is not None and boundary != head:
            fail(f"{pid}: closed transition has no promotion receipt "
                 f"(required from BUILD-{RECEIPT_REQUIRED_FROM:03d} once "
                 f"canonical history extends past closure)")
    return receipts, provenance


def read_evidence_any(pid: str, rec: dict) -> dict:
    """Load GateResult evidence: prefer the content-addressed object on
    the evidence ref; fall back to the in-history mirror under
    construction/evidence/ (required for CI and fresh clones — the
    platform blocks non-branch ref pushes; declared in
    BUILD-004-BOOTSTRAP-AMENDMENT-1). If both exist they must agree."""
    evidence_id = rec.get("evidence_object")
    ref_meta = None
    try:
        ref_meta = lib.read_evidence(evidence_id)
    except RuntimeError:
        pass
    mirror = ROOT / "construction" / "evidence" / f"{pid}.yaml"
    mirror_meta = load_yaml(mirror) if mirror.exists() else None
    if ref_meta is not None and mirror_meta is not None \
            and ref_meta != mirror_meta:
        fail(f"construction/evidence/{pid}.yaml: mirror does not equal the "
             f"evidence object {evidence_id}")
    meta = ref_meta if ref_meta is not None else mirror_meta
    if meta is None:
        raise RuntimeError(
            f"evidence object '{evidence_id}' unreadable and no mirror")
    return meta


def check_receipt_provenance(label: str, rec: dict) -> str:
    """Provenance of a schema-v2 receipt: recompute the authority
    identity from git objects and verify the bound evidence object."""
    ok = True
    try:
        derived = lib.derive_authority_identity(rec.get("parent_canonical", ""))
        if derived["identity"] != rec.get("authority_identity"):
            fail(f"{label}: authority_identity does not equal the value "
                 f"derived from git objects at parent_canonical "
                 f"({derived['identity']})")
            ok = False
    except RuntimeError as exc:
        fail(f"{label}: cannot derive authority identity: {exc}")
        ok = False
    try:
        meta = read_evidence_any(Path(label).stem, rec)
    except RuntimeError as exc:
        fail(f"{label}: GateResult evidence unreadable: {exc}")
        return "EVIDENCE_MISSING"
    for key in ("target_commit", "target_tree", "parent_canonical",
                "authority_identity", "environment_id"):
        if meta.get(key) != rec.get(key):
            fail(f"{label}: evidence object {key} '{meta.get(key)}' does "
                 f"not bind receipt value '{rec.get(key)}'")
            ok = False
    if meta.get("verdict") != rec.get("parent_law_verdict"):
        fail(f"{label}: evidence verdict '{meta.get('verdict')}' does not "
             f"bind receipt parent_law_verdict")
        ok = False
    if sorted(meta.get("expected_violations") or []) != \
            sorted(rec.get("expected_violations") or []):
        fail(f"{label}: evidence expected_violations do not bind receipt")
        ok = False
    return "EVIDENCE_BOUND" if ok else "EVIDENCE_CONFLICT"


# --- record checks -----------------------------------------------------------

def check_proposal(path: Path, schema: dict) -> dict:
    rec = load_yaml(path)
    label = str(path.relative_to(ROOT))
    check_required(rec, schema["required"], label)
    pid = rec.get("proposal", "")
    if isinstance(pid, str) and not re.fullmatch(schema["id_pattern"], pid):
        fail(f"{label}: id '{pid}' does not match {schema['id_pattern']}")
    if pid and path.stem != pid:
        fail(f"{label}: filename does not match proposal id '{pid}'")
    if isinstance(rec.get("budget"), dict):
        check_required(rec["budget"], schema["budget_required"], f"{label}.budget")
    return rec


def check_measured_keys(mapping: dict, derived: dict[str, str],
                        label: str) -> None:
    for key, value in mapping.items():
        if key in derived:
            if derived[key] != value:
                fail(f"{label}: '{key}: {value}' contradicts derived "
                     f"value '{derived[key]}'")
        elif not key.startswith("reported_"):
            fail(f"{label}: key '{key}' is neither derived by R_B/E_B nor "
                 f"marked reported_")


def check_grounding(path: Path, schema: dict, proposals: dict[str, dict],
                    derived_head: dict[str, str],
                    globals_cache: dict[str | None, dict[str, str]],
                    receipts: dict[str, dict]) -> None:
    rec = load_yaml(path)
    label = str(path.relative_to(ROOT))
    check_required(rec, schema["required"], label)
    pid = rec.get("proposal", "")
    if pid not in proposals:
        fail(f"{label}: references unknown proposal '{pid}'")
        return
    if path.stem != pid:
        fail(f"{label}: filename does not match proposal id '{pid}'")

    # Ledger-global keys are matched as of this grounding's closure
    # boundary (None = not yet committed: match against the present).
    boundary = adding_commit(f"construction/groundings/{pid}.yaml")
    if boundary not in globals_cache:
        globals_cache[boundary] = measure_globals(boundary, enforce=False)
    derived = dict(derived_head)
    derived.update(globals_cache[boundary])

    # Closure-bound experiment evidence (AUDIT-002 obligation 3): from
    # RECEIPT_BOUND_FROM, a transition's probe keys are matched against
    # the evidence its GateReceipt bound at closure — a present-time
    # rerun never silently redefines historical evidence. Legacy
    # transitions (< BUILD-003) remain matched against the present
    # rerun (grandfathered).
    receipt = receipts.get(pid)
    if receipt is not None and pid_number(pid) >= RECEIPT_BOUND_FROM:
        evidence = receipt.get("probe_evidence")
        if isinstance(evidence, dict):
            derived.update({k: str(v) for k, v in evidence.items()})

    predicted = rec.get("predicted")
    if predicted != proposals[pid].get("prediction"):
        fail(f"{label}: 'predicted' does not restate {pid}'s prediction "
             f"verbatim")
    observed = rec.get("observed")
    if isinstance(predicted, dict) and isinstance(observed, dict):
        missing = [k for k in predicted if k not in observed]
        if missing:
            fail(f"{label}: 'observed' missing predicted keys {missing}")

    fmt = rec.get("format", 1)
    if pid_number(pid) >= FORMAT2_FROM:
        if fmt < 2:
            fail(f"{label}: proposals >= BUILD-{FORMAT2_FROM:03d} require "
                 f"format >= 2")
        else:
            if isinstance(predicted, dict):
                check_measured_keys(predicted, derived, f"{label}.predicted")
            if isinstance(observed, dict):
                check_measured_keys(observed, derived, f"{label}.observed")
            evidence = rec.get("evidence", {})
            ref = evidence.get("proposal_commit") if isinstance(evidence, dict) else None
            true_commit = derived.get(f"proposal_commit_{pid}")
            if isinstance(ref, str) and true_commit:
                if pid_number(pid) >= CANONICAL_ID_FROM:
                    if ref != true_commit:
                        fail(f"{label}: evidence.proposal_commit '{ref}' is "
                             f"not the canonical commit identity "
                             f"'{true_commit}'")
                elif not true_commit.startswith(ref):
                    fail(f"{label}: evidence.proposal_commit '{ref}' does "
                         f"not match derived commit '{true_commit}'")
            # Reported gate verdicts are non-authoritative echoes: they
            # must reconcile with the external receipt (PRE-AUDIT-003
            # point 4), which is what P_B actually consumed.
            if receipt is not None and isinstance(observed, dict):
                for gkey, rkey in (
                        ("reported_parent_law_verdict", "parent_law_verdict"),
                        ("reported_prospective_law_verdict",
                         "prospective_law_verdict")):
                    if gkey in observed and \
                            observed[gkey] != receipt.get(rkey):
                        fail(f"{label}: '{gkey}: {observed[gkey]}' does not "
                             f"reconcile with receipt {rkey} "
                             f"'{receipt.get(rkey)}'")

    decision = rec.get("decision")
    if isinstance(decision, dict):
        check_required(decision, schema["decision_required"], f"{label}.decision")
        verdict = decision.get("verdict")
        if verdict not in schema["verdicts"]:
            fail(f"{label}: verdict '{verdict}' not in {schema['verdicts']}")


# --- main ---------------------------------------------------------------------

def main() -> int:
    proposal_schema = load_yaml(SCHEMAS / "build_proposal.schema.yaml")
    grounding_schema = load_yaml(SCHEMAS / "build_grounding.schema.yaml")
    registry = load_registry()

    proposals: dict[str, dict] = {}
    for path in sorted(PROPOSALS.glob("*.yaml")):
        rec = check_proposal(path, proposal_schema)
        if isinstance(rec.get("proposal"), str):
            proposals[rec["proposal"]] = rec

    if not proposals:
        fail("no proposals found: an empty ledger is not verifiable")
        for msg in FAILURES:
            print(f"FAIL {msg}")
        return 1

    grounding_paths = sorted(GROUNDINGS.glob("*.yaml")) if GROUNDINGS.exists() else []
    grounded = {p.stem for p in grounding_paths}

    attribution = attribute_commits(list(proposals))

    # R_B: passive derivation. Global laws are enforced at the present
    # state; per-grounding matching re-derives them at each closure
    # boundary (time-indexed measurement).
    derived: dict[str, str] = {}
    for pid, proposal in sorted(proposals.items()):
        derived.update(derive_transition(pid, proposal, attribution[pid],
                                         pid in grounded))
    now_globals = measure_globals(None, enforce=True)
    derived.update(now_globals)
    derived["environment_id"] = environment_id()
    derived.update(b003_bootstrap_discrepancy())

    # G_B evidence: promotion receipts, validated for provenance.
    receipts, provenance = check_receipts(proposals, grounded)
    for pid, status in provenance.items():
        derived[f"receipt_provenance_{pid}"] = status

    # E_B: experiments, registry-resolved, isolated.
    probe_names: set[str] = set()
    for pid, proposal in sorted(proposals.items()):
        probe_names.update(resolve_probes(pid, proposal.get("probes"),
                                          registry))
    derived.update(run_experiments(probe_names, registry))

    globals_cache: dict[str | None, dict[str, str]] = {None: now_globals}
    for path in grounding_paths:
        check_grounding(path, grounding_schema, proposals, derived,
                        globals_cache, receipts)

    for key in sorted(derived):
        print(f"derived {key} = {derived[key]}")
    for msg in FAILURES:
        print(f"FAIL {msg}")
    print(
        f"construction ledger: {len(proposals)} proposal(s), "
        f"{len(grounded)} grounding(s), {len(FAILURES)} violation(s)"
    )
    return 1 if FAILURES else 0


def reproduce() -> int:
    """Independent reproduction (AUDIT-003 obligation 3): re-execute the
    parent-law evaluation recorded by the newest schema-v2 receipt from
    frozen git objects and compare verdict and violation set against
    the bound evidence. Distinguishes authentic gate evidence from a
    fabricated PASS: a receipt whose target the parent law actually
    rejects cannot reproduce."""
    import gate  # deferred: only reproduction executes the gate
    candidates = sorted(RECEIPTS.glob("*.yaml")) if RECEIPTS.exists() else []
    newest = None
    for path in candidates:
        rec = load_yaml(path)
        if rec.get("schema_version", 1) >= 2:
            if newest is None or pid_number(path.stem) > pid_number(newest[0]):
                newest = (path.stem, rec)
    if newest is None:
        print("reproduce: no schema-v2 receipts to reproduce")
        return 0
    pid, rec = newest
    meta = read_evidence_any(pid, rec)
    result = gate.run_parent_law(rec["parent_canonical"],
                                 rec["target_commit"],
                                 rec.get("expected_violations") or [],
                                 transition=pid, emit_evidence=False)
    same_verdict = result["verdict"] == meta.get("verdict")
    same_violations = result["violations"] == (meta.get("violations") or [])
    if same_verdict and same_violations:
        print(f"reproduce {pid}: REPRODUCED "
              f"(verdict={result['verdict']}, "
              f"violations={len(result['violations'])})")
        return 0
    print(f"reproduce {pid}: DIVERGENT — live verdict "
          f"{result['verdict']} / violations {result['violations']} vs "
          f"evidence {meta.get('verdict')} / {meta.get('violations')}")
    return 1


if __name__ == "__main__":
    if "--reproduce" in sys.argv:
        sys.exit(reproduce())
    sys.exit(main())
