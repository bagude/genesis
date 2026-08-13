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

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "construction" / "schemas"
PROPOSALS = ROOT / "construction" / "proposals"
GROUNDINGS = ROOT / "construction" / "groundings"
REGISTRY = ROOT / "tools" / "probes.yaml"

RECORD_NAMESPACES = ("construction/proposals/", "construction/groundings/",
                     "construction/audits/")
IMPLICIT_SCOPE = RECORD_NAMESPACES
PROPOSAL_COMMIT_SCOPE = ("construction/proposals/", "construction/audits/")
TRAILER_RE = re.compile(r"^Construction-Transition:\s*(BUILD-\d{3})\s*$",
                        re.MULTILINE)
FORMAT2_FROM = 1        # first proposal whose grounding must be format 2
CANONICAL_ID_FROM = 2   # first proposal requiring full-SHA evidence identity
REGISTRY_ONLY_FROM = 2  # first proposal whose probes are names, not specs

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
        if not realization:
            derived[f"proposal_precedence_{pid}"] = "FAIL"
            fail(f"{pid}: grounded but no realization commit is attributed")
        elif all(is_strict_ancestor(pcommit, r) for r in realization):
            derived[f"proposal_precedence_{pid}"] = "PASS"
        else:
            derived[f"proposal_precedence_{pid}"] = "FAIL"
            fail(f"{pid}: proposal commit is not a strict ancestor of all "
                 f"realization commits")

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

    # Untracked commits beyond the measurement-law boundary.
    law_boundary = adding_commit("construction/groundings/BUILD-001.yaml")
    untracked = 0
    if law_boundary is not None and law_boundary in set(commits):
        for sha in commits:
            if sha == law_boundary or not is_strict_ancestor(law_boundary, sha):
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
                    globals_cache: dict[str | None, dict[str, str]]) -> None:
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

    # E_B: experiments, registry-resolved, isolated.
    probe_names: set[str] = set()
    for pid, proposal in sorted(proposals.items()):
        probe_names.update(resolve_probes(pid, proposal.get("probes"),
                                          registry))
    derived.update(run_experiments(probe_names, registry))

    globals_cache: dict[str | None, dict[str, str]] = {None: now_globals}
    for path in grounding_paths:
        check_grounding(path, grounding_schema, proposals, derived,
                        globals_cache)

    for key in sorted(derived):
        print(f"derived {key} = {derived[key]}")
    for msg in FAILURES:
        print(f"FAIL {msg}")
    print(
        f"construction ledger: {len(proposals)} proposal(s), "
        f"{len(grounded)} grounding(s), {len(FAILURES)} violation(s)"
    )
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
