"""Identity service: lifecycle of platform identities.

Creation is the only mutate path; identities are authenticated by their
keypairs (managed by the KeyManagementService) rather than passwords. Every
lifecycle change emits an audit event, guaranteeing a provable trail.

Role name vocabulary lives in ``qsmlops.security.permissions``; the service
accepts both custom strings and the built-in set. Unknown roles are rejected
by the permission model at check time, but we validate existence here too so
bad data never persists.
"""
from __future__ import annotations

import time

from qsmlops.core.errors import (
    IdentityAlreadyExistsError,
    IdentityError,
    NotFoundError,
    PermissionDeniedError,
)
from qsmlops.core.logging import get_logger
from qsmlops.database.repositories import IdentityRepository
from qsmlops.security.audit.events import AuditEvent
from qsmlops.security.audit.service import AuditService
from qsmlops.security.identity.models import (
    IDENTITY_KINDS,
    IDENTITY_STATUSES,
    Identity,
    KIND_AGENT,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    STATUS_REVOKED,
)
from qsmlops.security.permissions.model import ROLES, has_permission

log = get_logger(__name__)


class IdentityService:
    """Identity creation, authorization and deactivation."""

    def __init__(
        self,
        database,
        audit: AuditService,
        *,
        keystore=None,
        signature_service=None,
    ) -> None:
        self._repo = IdentityRepository(database)
        self._audit = audit
        self._keystore = keystore
        self._signature_service = signature_service

    # -------------------- creation --------------------
    def create_identity(
        self,
        kind: str,
        name: str,
        owner: str,
        role: str = "",
        *,
        permissions: set[str] | None = None,
        description: str = "",
        metadata: dict | None = None,
    ) -> Identity:
        if kind not in IDENTITY_KINDS:
            raise IdentityError(f"invalid identity kind {kind!r}")
        if role and role not in ROLES:
            raise IdentityError(f"unknown role {role!r}; define it in the permission model first")
        identity = Identity(
            kind=kind,
            name=name,
            owner=owner,
            role=role,
            permissions=permissions,
            description=description,
            metadata=metadata,
            status=STATUS_ACTIVE,
        )
        identity.compute_hash()
        # Optional key issuance for principals that will sign as themselves.
        if kind != KIND_AGENT and self._keystore is not None:
            try:
                from qsmlops.crypto.agility import AgilityEngine

                agility = AgilityEngine()
                suite = agility.select_suite()
                self._keystore.generate_keypair(
                    "SIGNER", suite.signature_algorithm, owner=identity.display
                )
            except Exception as exc:  # key issuance is best-effort in Phase 1
                log.warning("identity key issuance failed for %s: %s", identity.display, exc)
        try:
            self._repo.insert(identity)
        except IdentityError:
            raise IdentityAlreadyExistsError(
                f"identity {kind}:{name} already exists"
            )
        self._audit.record(
            AuditEvent.from_object(
                identity,
                actor=owner or "system",
                action="identity.created",
                metadata={"kind": kind, "role": role},
            )
        )
        return identity

    # -------------------- lookup --------------------
    def get(self, identity_id: str) -> Identity:
        identity = self._repo.get(identity_id)
        if identity is None:
            raise NotFoundError(f"identity {identity_id} not found")
        return identity

    def find(self, kind: str, name: str) -> Identity | None:
        return self._repo.find_by_name(kind, name)

    def list(
        self, kind: str | None = None, status: str | None = None
    ) -> list[Identity]:
        return self._repo.list(kind=kind, status=status)

    # -------------------- authorization --------------------
    def authorize(self, identity: Identity | str, permission: str) -> Identity:
        """Return the identity iff it holds the permission; raise otherwise."""
        if isinstance(identity, str):
            identity = self.get(identity)
        if not identity.is_active():
            raise PermissionDeniedError(f"identity {identity.name!r} is not active")
        identity.require_permission(permission)
        return identity

    # -------------------- lifecycle --------------------
    def set_status(
        self,
        identity_id: str,
        status: str,
        *,
        actor: str = "system",
        reason: str = "",
    ) -> Identity:
        if status not in IDENTITY_STATUSES:
            raise IdentityError(f"invalid status {status!r}")
        identity = self.get(identity_id)
        if identity.status == STATUS_REVOKED and status != STATUS_REVOKED:
            raise IdentityError("revoked identities cannot be re-activated")
        identity.status = status
        identity.updated_at = time.time()
        identity.version += 1
        identity.compute_hash()
        self._repo.update(identity)
        self._audit.record(
            AuditEvent.from_object(
                identity,
                actor=actor,
                action=f"identity.status.{status.lower()}",
                metadata={"reason": reason},
            )
        )
        return identity

    def deactivate(self, identity_id: str, *, actor: str = "system") -> Identity:
        return self.set_status(identity_id, STATUS_INACTIVE, actor=actor)

    def revoke(self, identity_id: str, *, actor: str = "system", reason: str = "") -> Identity:
        return self.set_status(identity_id, STATUS_REVOKED, actor=actor, reason=reason)

    def grant_permissions(
        self,
        identity_id: str,
        permissions: set[str],
        *,
        actor: str = "system",
    ) -> Identity:
        identity = self.get(identity_id)
        identity.permissions |= set(permissions)
        identity.updated_at = time.time()
        identity.version += 1
        identity.compute_hash()
        self._repo.update(identity)
        self._audit.record(
            AuditEvent.from_object(
                identity,
                actor=actor,
                action="identity.permissions.granted",
                metadata={"permissions": sorted(permissions)},
            )
        )
        return identity

    def revoke_permissions(
        self,
        identity_id: str,
        permissions: set[str],
        *,
        actor: str = "system",
    ) -> Identity:
        identity = self.get(identity_id)
        identity.permissions -= set(permissions)
        identity.updated_at = time.time()
        identity.version += 1
        identity.compute_hash()
        self._repo.update(identity)
        self._audit.record(
            AuditEvent.from_object(
                identity,
                actor=actor,
                action="identity.permissions.revoked",
                metadata={"permissions": sorted(permissions)},
            )
        )
        return identity
