# Trust Model

## Roots of trust

1. **Trust anchors** (`trust_anchors.json`) — public keys registered by the
   KeyStore. Verification always resolves keys through
   `trusted_public_key(key_id)`, which refuses revoked or expired anchors.
2. **Content addressing** — the ArtifactStore addresses bytes by their
   SHA3-256 digest; any modification invalidates the address, so declared
   digests are self-verifying references.

## Chain of trust for a model version

```
trust anchor (signer key)
  └─ signs → passport (canonical JSON, ML-DSA)
       ├─ binds → artifact digest   (model bytes)
       ├─ binds → BOM digest        (QML-BOM: dataset/code/framework/artifact)
       └─ binds → training info + metrics + environment
```

Every hop is verified before use:

* **Registration** — `registry.register` records digests; verification
  packets capture per-agent security checks.
* **Deployment gate** — state machine transitions
  (REGISTERED → VERIFIED → APPROVED → DEPLOYED) require signature validity,
  successful verification and **separation of duties**: the verifier must
  differ from the signer.
* **Serving** — `ModelDeploymentService.load` re-verifies the passport on
  every cold load; revoked signing keys raise `ServingError("revoked")`,
  expired ones `ServingError("expired")`.

## Identity trust

Identities (human / service / agent) are TrustedObjects whose status governs
authorization: only `active` identities may act, and revocation is terminal.
See [CRYPTOGRAPHIC_IDENTITY.md](CRYPTOGRAPHIC_IDENTITY.md).

## Policy as trust enforcement

The declarative policy engine converts observed facts into decisions:
broken trust chains block deployment (gate rules), critical non-drift
findings quarantine, critical drift on an active deployment rolls back.
Rules are data — organization policy sets can be edited and hot-reloaded
without code changes (`qsmlops/security/policies/loader.py`).

## Trust boundaries

* The evidence ledger is append-only and hash-chained; tampering with any
  historical entry breaks chain verification.
* Agent findings are evidence-backed; agent crash is itself recorded as a
  failed finding rather than silently ignored.
* PQC guarantees hold only for artifacts that flow through the enforced
  paths above; out-of-band artifact edits are detectable but not preventable.
