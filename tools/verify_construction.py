#!/usr/bin/env python3
"""Construction-ledger verifier (law for construction/ records).

v2 (BUILD-001, AUDIT-000 repair). Beyond the structural laws of v1,
R_B now DERIVES the following from repository evidence instead of
accepting reported values:

  * ProposalPrecedence — the proposal commit is a strict git ancestor
    of every realization commit of its transition
  * ScopeConformance  — union of realization-commit diffs lies within
    allowed_scope plus the implicit record paths
  * BudgetConformance — distinct files across all transition commits
    <= budget.max_files_changed
  * ProbeResults      — probes declared in proposals are executed here
  * EvidenceProvenance — evidence commit references must match derived
    attribution

Attribution: commits carry a "Construction-Transition: BUILD-NNN"
trailer; the proposal commit is the commit adding the proposal file and
may touch only construction/proposals/ and construction/audits/.
Legacy pre-BUILD-001 commits are attributed by the record files they
touch (grandfather clause).

Groundings for BUILD-001 onward declare `format: 2`: every predicted /
observed key must either belong to the derived vocabulary (and equal
the derived value byte-for-byte) or be prefixed `reported_`, marking it
explicitly as non-measured.

Lifecycle: a proposal without a grounding is OPEN; at most one OPEN
proposal may exist and it must be the highest-numbered one. Every
commit descending from the BUILD-001 realization must carry a
transition trailer.

Exit code 0 means the construction ledger is law-conformant.
Stdlib + pyyaml only, by declaration of BUILD-000/BUILD-001.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "construction" / "schemas"
PROPOSALS = ROOT / "construction" / "proposals"
GROUNDINGS = ROOT / "construction" / "groundings"

# Paths any transition may touch regardless of allowed_scope.
IMPLICIT_SCOPE = ("construction/proposals/", "construction/groundings/",
                  "construction/audits/")
PROPOSAL_COMMIT_SCOPE = ("construction/proposals/", "construction/audits/")
TRAILER_RE = re.compile(r"^Construction-Transition:\s*(BUILD-\d{3})\s*$",
                        re.MULTILINE)
# First proposal whose grounding must use format 2 derived vocabulary.
FORMAT2_FROM = 1

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


# --- repository evidence -------------------------------------------------

def all_commits() -> list[str]:
    out = git("log", "--format=%H")
    return out.split("\n") if out else []


def commit_files(sha: str) -> list[str]:
    out = git("show", "--name-only", "--format=", sha)
    return [line for line in out.split("\n") if line]


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


def run_probe(cmd: str, expect_exit: int) -> str:
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True,
                             cwd=ROOT, timeout=300)
        return "PASS" if res.returncode == expect_exit else "FAIL"
    except subprocess.TimeoutExpired:
        return "FAIL"


# --- derivation (R_B) -----------------------------------------------------

def derive_transition(pid: str, proposal: dict, commits: set[str],
                      has_grounding: bool) -> dict[str, str]:
    """Derive the measured properties of one transition from git."""
    derived: dict[str, str] = {}
    pcommit = adding_commit(f"construction/proposals/{pid}.yaml")
    if pcommit is None:
        fail(f"{pid}: proposal file has no adding commit in history")
        return derived
    derived[f"proposal_commit_{pid}"] = pcommit[:7]

    # Proposal-commit content law.
    bad = [f for f in commit_files(pcommit)
           if not f.startswith(PROPOSAL_COMMIT_SCOPE)]
    if bad:
        fail(f"{pid}: proposal commit {pcommit[:7]} touches non-proposal "
             f"paths {bad}")

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

    # Scope conformance over realization diffs.
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

    # Budget over all transition commits.
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

    # Probes are executed here, never taken from the narrative.
    for probe in proposal.get("probes", []) or []:
        name, cmd = probe.get("name"), probe.get("cmd")
        expect = probe.get("expect_exit", 0)
        if not isinstance(name, str) or not isinstance(cmd, str):
            fail(f"{pid}: malformed probe entry {probe}")
            continue
        result = run_probe(cmd, expect)
        derived[f"probe_{name}"] = result
        if result != "PASS":
            fail(f"{pid}: probe '{name}' failed ({cmd})")

    return derived


# --- record checks --------------------------------------------------------

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
                        globals_: dict[str, str], label: str) -> None:
    """Format-2 law: keys are derived-vocabulary (and must match) or
    explicitly reported_."""
    for key, value in mapping.items():
        if key in derived:
            if derived[key] != value:
                fail(f"{label}: '{key}: {value}' contradicts derived "
                     f"value '{derived[key]}'")
        elif key in globals_:
            if globals_[key] != value:
                fail(f"{label}: '{key}: {value}' contradicts derived "
                     f"value '{globals_[key]}'")
        elif not key.startswith("reported_"):
            fail(f"{label}: key '{key}' is neither derived by R_B nor "
                 f"marked reported_")


def check_grounding(path: Path, schema: dict, proposals: dict[str, dict],
                    derived: dict[str, str], globals_: dict[str, str]) -> None:
    rec = load_yaml(path)
    label = str(path.relative_to(ROOT))
    check_required(rec, schema["required"], label)
    pid = rec.get("proposal", "")
    if pid not in proposals:
        fail(f"{label}: references unknown proposal '{pid}'")
        return
    if path.stem != pid:
        fail(f"{label}: filename does not match proposal id '{pid}'")

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
                check_measured_keys(predicted, derived, globals_,
                                    f"{label}.predicted")
            if isinstance(observed, dict):
                check_measured_keys(observed, derived, globals_,
                                    f"{label}.observed")
            evidence = rec.get("evidence", {})
            ref = evidence.get("proposal_commit") if isinstance(evidence, dict) else None
            true_commit = derived.get(f"proposal_commit_{pid}")
            if isinstance(ref, str) and true_commit and \
                    not (ref.startswith(true_commit) or true_commit.startswith(ref)):
                fail(f"{label}: evidence.proposal_commit '{ref}' does not "
                     f"match derived commit '{true_commit}'")

    decision = rec.get("decision")
    if isinstance(decision, dict):
        check_required(decision, schema["decision_required"], f"{label}.decision")
        verdict = decision.get("verdict")
        if verdict not in schema["verdicts"]:
            fail(f"{label}: verdict '{verdict}' not in {schema['verdicts']}")


# --- global laws ----------------------------------------------------------

def check_lifecycle(proposals: dict[str, dict], grounded: set[str]) -> str:
    open_ = sorted(set(proposals) - grounded)
    if len(open_) > 1:
        fail(f"lifecycle: more than one OPEN proposal: {open_}")
    if open_ and proposals:
        newest = max(proposals, key=pid_number)
        if open_[0] != newest:
            fail(f"lifecycle: OPEN proposal {open_[0]} is not the "
                 f"highest-numbered ({newest})")
    return str(len(open_))


def check_untracked_commits() -> str:
    """Every commit descending from the BUILD-001 realization must carry a
    transition trailer."""
    boundary = adding_commit("construction/groundings/BUILD-001.yaml")
    if boundary is None:
        return "0"
    untracked = 0
    for sha in all_commits():
        if sha == boundary or not is_strict_ancestor(boundary, sha):
            continue
        if commit_trailer(sha) is None:
            untracked += 1
            fail(f"commit {sha[:7]}: descends from measurement-law boundary "
                 f"but carries no Construction-Transition trailer")
    return str(untracked)


# --- main -----------------------------------------------------------------

def main() -> int:
    proposal_schema = load_yaml(SCHEMAS / "build_proposal.schema.yaml")
    grounding_schema = load_yaml(SCHEMAS / "build_grounding.schema.yaml")

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
    derived: dict[str, str] = {}
    for pid, proposal in sorted(proposals.items()):
        derived.update(derive_transition(pid, proposal, attribution[pid],
                                         pid in grounded))

    globals_ = {
        "open_proposals": check_lifecycle(proposals, grounded),
        "untracked_commits": check_untracked_commits(),
    }

    for path in grounding_paths:
        check_grounding(path, grounding_schema, proposals, derived, globals_)

    for key in sorted(derived):
        print(f"derived {key} = {derived[key]}")
    for key in sorted(globals_):
        print(f"derived {key} = {globals_[key]}")
    for msg in FAILURES:
        print(f"FAIL {msg}")
    print(
        f"construction ledger: {len(proposals)} proposal(s), "
        f"{len(grounded)} grounding(s), {len(FAILURES)} violation(s)"
    )
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
