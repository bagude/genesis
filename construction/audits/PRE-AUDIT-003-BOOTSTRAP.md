# PRE-AUDIT-003-BOOTSTRAP — Frozen bootstrap authority for BUILD-003

One-transition bootstrap binding, required by PRE-AUDIT-003's final
condition. Additions-only; the frozen BUILD-003 proposal is not
modified. Invariant established here:

    Identity(A_t) is fixed before Candidate_{t+1} exists,
    and A_003_parent != A_004_candidate.

## Binding

bootstrap_transition: BUILD-003

parent_canonical_identity:
    The commit that introduces this record: the unique child of
    fb4e201139499afb9e1119d226491778ba67809f whose diff adds exactly
    construction/audits/PRE-AUDIT-003-BOOTSTRAP.md. A commit cannot
    contain its own hash; this identity is fixed by git content
    addressing the moment the record is committed, is reported in the
    construction dialogue at freeze time, and is derivable forever as
    the adding commit of this file. Candidate/BUILD-003 branches from
    exactly that commit. That state contains the frozen proposal
    7c90a23f..., AUDIT-002, PRE-AUDIT-003, and this binding, and
    contains NO tools/authority.yaml.

parent_law_origin:
    BUILD-002 / 409be0c6ee343ce4d3718c02a9a2b2e334090feb
    (the transition that realized the law bundle; bundle blobs verified
    byte-identical between 409be0c and fb4e201 before this freeze)

parent_authority_members:
    - path: tools/verify_construction.py
      blob: c495d9ffaa7e89f6b210de8672b4a034f3227bbb
    - path: tools/probes.yaml
      blob: 01eb084c0d6b856d5b80da368abad96d2cf7e57b
    - path: construction/schemas/build_proposal.schema.yaml
      blob: a706e30ba7dae9bd17b6114144bbe3d2a123d870
    - path: construction/schemas/build_grounding.schema.yaml
      blob: dcadfd1efa6a3981883b570a876c58662ef74ddc

parent_authority_identity:
    sha256 over the sorted "<blob> <path>" lines of
    parent_authority_members:
    a498931e482a1022e03f80f3291d75f28177363e5f65ee05d42a1a10a69ad4ac

bootstrap_issuer:
    The repository steward (bagude), acting through the external
    audit channel that issued AUDIT-002, PRE-AUDIT-003, and this
    bootstrap condition. This principal precedes and is not derived
    from any candidate BUILD-003 state. The builder session (Claude,
    session 019M1VEWpY6pk11w6aPpxXC6) is executor only, not issuer.

receipt_provenance:
    The authoritative GateReceipt for BUILD-003 may be issued only by
    the bootstrap gate ceremony: execution of the
    parent_authority_members listed above — extracted from
    parent_canonical_identity by git plumbing and verified against the
    blob identities in this record — against the finalized
    candidate/BUILD-003 commit, performed by the builder session as
    executor under the bootstrap_issuer's authority declared here.
    Issuer(receipt) is therefore A_003_parent as frozen in this record;
    no artifact contained in candidate BUILD-003 participates in
    issuing it.

candidate_manifest_rule:
    tools/authority.yaml contained in C_003 is prospective A_{t+1}
    ONLY. It MUST NOT participate in selecting or validating A_t for
    BUILD-003 admission. Its first authoritative use is defining A_t
    for BUILD-004 admission, read from the accepted post-promotion
    canonical state.

receipt_append_authorization:
    The post-promotion receipt-only commit is an authorized consequence
    of the Gate/promotion ceremony declared above, performed by the
    same executor immediately after fast-forward promotion, restricted
    to additions under construction/receipts/, carrying the trailer
    "Construction-Receipt: BUILD-003". Any canonical mutation outside
    this restriction is an unaccounted mutation and a ledger violation.

## Scope note

This binding is valid for exactly one transition (BUILD-003). From the
accepted BUILD-003 state onward, tools/authority.yaml at the accepted
canonical HEAD mechanically defines A_t for BUILD-004 and subsequent
generations.
