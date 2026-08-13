#!/usr/bin/env python3
"""Construction-ledger verifier (law for construction/ records).

Enforces the structural and cross-record laws of construction/ALGEBRA.md:

  * every proposal and grounding matches its structural schema
  * every grounding references an existing proposal
  * grounding.predicted equals the proposal's prediction verbatim
  * grounding.observed covers every predicted key
  * decision.verdict is a declared verdict

Exit code 0 means the construction ledger is law-conformant.
Stdlib + pyyaml only, by declaration of BUILD-000.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "construction" / "schemas"
PROPOSALS = ROOT / "construction" / "proposals"
GROUNDINGS = ROOT / "construction" / "groundings"

FAILURES: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)


def load_yaml(path: Path) -> dict:
    with path.open() as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        fail(f"{path}: top level is not a mapping")
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


def check_grounding(path: Path, schema: dict, proposals: dict[str, dict]) -> None:
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
    prediction = proposals[pid].get("prediction")
    if predicted != prediction:
        fail(f"{label}: 'predicted' does not restate {pid}'s prediction verbatim")
    observed = rec.get("observed")
    if isinstance(predicted, dict) and isinstance(observed, dict):
        missing = [k for k in predicted if k not in observed]
        if missing:
            fail(f"{label}: 'observed' missing predicted keys {missing}")
    decision = rec.get("decision")
    if isinstance(decision, dict):
        check_required(decision, schema["decision_required"], f"{label}.decision")
        verdict = decision.get("verdict")
        if verdict not in schema["verdicts"]:
            fail(f"{label}: verdict '{verdict}' not in {schema['verdicts']}")


def main() -> int:
    proposal_schema = load_yaml(SCHEMAS / "build_proposal.schema.yaml")
    grounding_schema = load_yaml(SCHEMAS / "build_grounding.schema.yaml")

    proposals: dict[str, dict] = {}
    for path in sorted(PROPOSALS.glob("*.yaml")):
        rec = check_proposal(path, proposal_schema)
        if isinstance(rec.get("proposal"), str):
            proposals[rec["proposal"]] = rec

    grounded: set[str] = set()
    if GROUNDINGS.exists():
        for path in sorted(GROUNDINGS.glob("*.yaml")):
            check_grounding(path, grounding_schema, proposals)
            grounded.add(path.stem)

    if not proposals:
        fail("no proposals found: an empty ledger is not verifiable")

    for msg in FAILURES:
        print(f"FAIL {msg}")
    print(
        f"construction ledger: {len(proposals)} proposal(s), "
        f"{len(grounded)} grounding(s), {len(FAILURES)} violation(s)"
    )
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
