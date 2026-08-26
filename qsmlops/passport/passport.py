"""Quantum Secure Model Passport: cryptographic identity for every model.

The passport is a canonical JSON document signed with ML-DSA. It binds model
identity, dataset provenance, training info, code version, environment,
metrics, security status and deployment history into one signed object. The
signature covers the document digest; verification always goes through the
KeyStore trust anchors, never through presence of the file.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from qsmlops.crypto.agility import AgilityEngine
from qsmlops.crypto.hashing import digest_document
from qsmlops.crypto.keys import KeyStore
from qsmlops.crypto.providers import SIGNATURE_PROVIDERS, ProviderError

PASSPORT_SCHEMA_VERSION = "1.0"


class PassportError(Exception):
    pass


@dataclass
class SignatureBlock:
    suite_id: str
    algorithm_id: str
    signer_key_id: str
    signature_hex: str
    signed_digest: str
    signed_at: float


@dataclass
class Passport:
    schema_version: str
    passport_id: str
    created_at: float

    identity: dict = field(default_factory=dict)
    dataset_provenance: dict = field(default_factory=dict)
    training_info: dict = field(default_factory=dict)
    code_version: dict = field(default_factory=dict)
    environment: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    security_status: dict = field(default_factory=dict)
    deployment_history: list = field(default_factory=list)

    signature: SignatureBlock | None = None

    def body(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "passport_id": self.passport_id,
            "created_at": self.created_at,
            "identity": self.identity,
            "dataset_provenance": self.dataset_provenance,
            "training_info": self.training_info,
            "code_version": self.code_version,
            "environment": self.environment,
            "metrics": self.metrics,
            "security_status": self.security_status,
            "deployment_history": self.deployment_history,
        }

    def to_dict(self) -> dict:
        doc = self.body()
        doc["signature"] = (
            {
                "suite_id": self.signature.suite_id,
                "algorithm_id": self.signature.algorithm_id,
                "signer_key_id": self.signature.signer_key_id,
                "signature_hex": self.signature.signature_hex,
                "signed_digest": self.signature.signed_digest,
                "signed_at": self.signature.signed_at,
            }
            if self.signature
            else None
        )
        return doc

    @classmethod
    def from_dict(cls, d: dict) -> "Passport":
        sig = d.get("signature")
        return cls(
            schema_version=d.get("schema_version", PASSPORT_SCHEMA_VERSION),
            passport_id=d["passport_id"],
            created_at=d["created_at"],
            identity=d.get("identity", {}),
            dataset_provenance=d.get("dataset_provenance", {}),
            training_info=d.get("training_info", {}),
            code_version=d.get("code_version", {}),
            environment=d.get("environment", {}),
            metrics=d.get("metrics", {}),
            security_status=d.get("security_status", {}),
            deployment_history=d.get("deployment_history", []),
            signature=SignatureBlock(**sig) if sig else None,
        )

    def digest(self) -> str:
        return digest_document(self.body())

    def sign(
        self,
        keystore: KeyStore,
        agility: AgilityEngine,
        signer_owner: str,
        suite_id: str | None = None,
    ) -> None:
        if self.signature is not None:
            raise PassportError("passport already signed; issue a new version instead")
        suite = agility.select_suite(suite_id or agility.default_suite)
        agility.assert_usable(suite)
        provider = SIGNATURE_PROVIDERS[suite.signature_algorithm]
        key_id, secret_key = keystore.active_signing_key(signer_owner)
        record = keystore.get_record(key_id)
        if record.algorithm_id != suite.signature_algorithm:
            raise ProviderError(
                f"active key {key_id} uses {record.algorithm_id}, "
                f"suite requires {suite.signature_algorithm}"
            )
        doc_digest = self.digest()
        sig = provider.sign(secret_key, doc_digest.encode())
        self.signature = SignatureBlock(
            suite_id=suite.suite_id,
            algorithm_id=suite.signature_algorithm,
            signer_key_id=key_id,
            signature_hex=sig.hex(),
            signed_digest=doc_digest,
            signed_at=time.time(),
        )

    def verify_signature(self, keystore: KeyStore) -> bool:
        if self.signature is None:
            return False
        try:
            record = keystore.get_record(self.signature.signer_key_id)
        except KeyError:
            return False
        if record.status in ("revoked", "expired"):
            return False
        provider = SIGNATURE_PROVIDERS.get(record.algorithm_id)
        if provider is None:
            return False
        try:
            public_key = keystore.trusted_public_key(self.signature.signer_key_id)
        except Exception:
            # Expired/unknown key records surface here; treat as invalid rather
            # than propagating an exception (fail-closed, never fail-open).
            return False
        recomputed = self.digest()
        if recomputed != self.signature.signed_digest:
            return False
        try:
            return provider.verify(
                public_key,
                recomputed.encode(),
                bytes.fromhex(self.signature.signature_hex),
            )
        except Exception:
            return False

    def add_deployment_event(self, event: dict) -> "Passport":
        """Returns a new unsigned passport carrying the appended history.

        Signing is over the full document, so any change to the deployment
        history invalidates the old signature by construction; the platform
        therefore re-issues (re-signs) the passport as a new revision.
        """
        import copy

        clone = copy.deepcopy(self)
        clone.signature = None
        clone.deployment_history.append(event)
        return clone


def new_passport(
    name: str,
    version: int,
    owner: str,
    bom_digest: str,
    artifact_digest: str,
    training_info: dict | None = None,
    metrics: dict | None = None,
    environment: dict | None = None,
    security_status: dict | None = None,
    dataset_provenance: dict | None = None,
) -> Passport:
    return Passport(
        schema_version=PASSPORT_SCHEMA_VERSION,
        passport_id=uuid.uuid4().hex,
        created_at=time.time(),
        identity={
            "name": name,
            "version": version,
            "owner": owner,
            "artifact_digest": artifact_digest,
        },
        dataset_provenance=dict(dataset_provenance or {"bom_digest": bom_digest}),
        training_info=dict(training_info or {}),
        code_version={"bom_digest": bom_digest},
        environment=dict(environment or {}),
        metrics=dict(metrics or {}),
        security_status=dict(security_status or {"state": "PENDING_REVIEW"}),
        deployment_history=[],
    )


def _public_of(keystore: KeyStore, key_id: str) -> str:
    rec = keystore._read_json(keystore._anchors_path)[key_id]
    return rec["public_key_hex"]
