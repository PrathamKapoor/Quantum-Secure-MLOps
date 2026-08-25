# Phase 6 Implementation: Secure Model Deployment / Governed Serving

> Specification: architecture document PART 14 §14.3 (PHASE 6), PART 21
> STAGE 6, PART 23 §23.16; detail §7.11 (Action Controller), §8 (Self-Healing),
> §9.10 (deployment trust gates).

## Objective

Deployment request → model/version resolution → registry state validation →
cryptographic gates → Phase-5 trust eligibility → environment validation →
policy/authorization → **registry.deploy() (sole promotion)** → serving state →
post-deployment verification → audit evidence.

## State on entry

`serving/deployment.py` + `serving/environment.py` existed from the
interrupted session: compiled but unwired, and `deployment.py` carried two
defects (orphaned dead code inside `_deny`; missing `_resolve_version` that
`request()` calls).

## Implemented

1. **Repairs**: restored `_resolve_version`; removed dead code/walrus/redundant
   exception tuple; unknown-version now produces an audited structured denial.
2. **Wiring**: `SelfHealingMLOps.deployments = DeploymentService(registry)`;
   pipeline delegates `request_deployment()` / `validate_deployment()`.
3. **API** (`api/app.py`): `POST /deployment/request` (409 + structured details
   on refusal), `GET /deployment/status/{model}` (active deployment + serving
   health probe via existing gates), `GET /deployment/validation/{version_id}`
   (dry run), `POST /deployment/rollback/{model}` (existing registry rollback).
4. **CLI**: `request-deployment`, `validate-deployment`, `deployment-status`
   — same service layer as the API.
5. **Environment validation** (`environment.py`, pre-existing, now exercised):
   declared-vs-actual Python runtime, BOM dependency pins vs installed
   versions, hardware declarations; anything unmeasurable is reported
   UNVERIFIABLE — never silently accepted.

## Security invariants preserved

- `registry.deploy()` remains the only promotion mechanism; the service never
  mutates registry state directly.
- Trust is consumed, never recomputed: `promotion_eligible` + decision from
  the Phase-5 evaluation; BLOCKED / QUARANTINED / REVIEW_REQUIRED all refuse.
- Cryptographic gates re-checked per request: signature vs trust anchors,
  artifact integrity, signer status/expiry.
- Authorization: non-empty actor identity + separation of duties (deploying
  actor ≠ signer owner) + default PolicyEngine deployment gates over trust/
  signature facts.
- Every outcome ledgered: `deployment_requested` / `deployment_validation` /
  `deployment_denied` / `deployment_completed` /
  `deployment_failed_postverification`.

## Gate-D security prerequisite (same session)

Encrypted keystore selection: when `QSMLOPS_KEYSTORE_PASSPHRASE` is set, the
platform opens `EncryptedKeyStore` (AES-256-GCM vault); any legacy plaintext
`secret_keys.json` is migrated into the vault and deleted (pre-existing vault
capability, newly wired). Without the variable, legacy development behavior is
unchanged (documented compatibility). Proven by
`tests/test_keystore_remediation.py` (vault created, plaintext absent,
retrieval/sign/verify across reopen, wrong-passphrase fail-closed).

## Verification

| Suite | Result |
|---|---|
| New `tests/test_phase6_deployment_flow.py` | 16/16 |
| Full core suite | **208 passed** (188 prior + 4 keystore + 16 phase-6) |
| compileall | clean |
| demo.py | SUCCESS (chain OK) |
| CLI smoke | DENIED-before-approval → DEPLOYED+serving_healthy → status TRUSTED |

## Limitations

- Environment validation covers runtime/dependencies/hardware declarations;
  network/TLS/cloud targets out of scope by design.
- Post-deployment verification uses the existing serving gates + active-
  deployment match; no synthetic inference probe is executed.
- Encrypted keystore requires the operator to supply the passphrase env var;
  no HSM/KMS integration (roadmap Phase 13+).

## Status: COMPLETE (within Phase-6 scope)
