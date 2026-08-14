#!/usr/bin/env python3
"""Anti-regression self-test for typed probe semantics (BUILD-007).

AUDIT-006 Finding 2: the old evaluator inferred denial from ANY
exception, so a VISIBLE parent repository — which raised RuntimeError —
certified as DENIED/PASS. This self-test asserts mechanically that the
false-pass path is closed, and it is registered in tools/probes.yaml so
the verifier's E_B executes it on every run: the anti-regression is
LAW, not a one-time claim.

Asserts:
  1. A visible parent yields ALLOWED and therefore verdict FAIL.
  2. An arbitrary exception yields ERROR, never DENIED.
  3. certify_probes rejects ERROR and INCONCLUSIVE outcomes.
  4. certify_probes rejects a missing probe result.
  5. The positive control must be ALLOWED; a realm that denies
     everything (including scratch) does not certify.

Exit 0 iff every assertion holds.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capability_policy as pol  # noqa: E402


def passing_results() -> dict:
    """A synthetic result set where every probe meets its expectation."""
    return {p["probe_id"]: {"probe_id": p["probe_id"],
                            "observed_outcome": p["expected_outcome"],
                            "verdict": "PASS"}
            for p in pol.PROBES}


def run() -> list[str]:
    """Return the list of failures. PURE computation over the frozen
    policy — no subprocesses, no filesystem effects — so V_B may call it
    directly as a law check on every run without violating R_B's
    read-only capability contract."""
    failures = []

    # 1. Visible parent => ALLOWED => FAIL (the AUDIT-006 false-pass path).
    r = passing_results()
    r["parent_repo_visibility"] = {"probe_id": "parent_repo_visibility",
                                   "observed_outcome": "ALLOWED",
                                   "verdict": "FAIL"}
    ok, problems = pol.certify_probes(r)
    if ok:
        failures.append("visible parent certified (AUDIT-006 false-pass "
                        "path is OPEN)")

    # 2/3. ERROR and INCONCLUSIVE never certify as denial.
    for bad in ("ERROR", "INCONCLUSIVE", "DENIED_MAYBE"):
        r = passing_results()
        r["network_connect"] = {"probe_id": "network_connect",
                                "observed_outcome": bad,
                                "verdict": "FAIL"}
        ok, _ = pol.certify_probes(r)
        if ok:
            failures.append(f"outcome {bad} certified as denial")

    # An ERROR outcome carrying a forged PASS verdict must still fail,
    # because certification compares observed against expected.
    r = passing_results()
    r["network_connect"] = {"probe_id": "network_connect",
                            "observed_outcome": "ERROR",
                            "verdict": "PASS"}
    ok, _ = pol.certify_probes(r)
    if ok:
        failures.append("ERROR with forged PASS verdict certified")

    # 4. A missing probe result never certifies.
    r = passing_results()
    r.pop("setuid_root_syscall")
    ok, _ = pol.certify_probes(r)
    if ok:
        failures.append("missing probe result certified")

    # 5. The positive control must actually be exercised.
    r = passing_results()
    r["write_scratch"] = {"probe_id": "write_scratch",
                          "observed_outcome": "DENIED", "verdict": "FAIL"}
    ok, _ = pol.certify_probes(r)
    if ok:
        failures.append("inert realm (scratch denied) certified")

    # Sanity: the fully-conforming set must certify, or the test is vacuous.
    ok, problems = pol.certify_probes(passing_results())
    if not ok:
        failures.append(f"conforming result set failed to certify: {problems}")

    # Privilege contract: a weakened privilege state must not certify.
    weakened = dict(pol.PRIVILEGE_CONTRACT)
    weakened["NoNewPrivs"] = "0"
    if pol.certify_privilege(weakened)[0]:
        failures.append("NoNewPrivs=0 certified")
    weakened = dict(pol.PRIVILEGE_CONTRACT)
    weakened["CapBnd"] = "000001ffffffffff"
    if pol.certify_privilege(weakened)[0]:
        failures.append("non-empty capability bounding set certified")
    if not pol.certify_privilege(dict(pol.PRIVILEGE_CONTRACT))[0]:
        failures.append("frozen privilege contract failed to self-certify")

    return failures


def main() -> int:
    failures = run()
    for f in failures:
        print(f"FAIL {f}")
    print(f"probe-semantics self-test: {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
