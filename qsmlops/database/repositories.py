"""Repository pattern over the platform database.

Repositories encapsulate all SQL; services never touch the engine directly
for entity operations. Documents are stored canonically JSON-serialized in
TEXT columns (the tables are mirrors/indexes — the ledger is the evidence
source of truth).
"""
from __future__ import annotations

import json
from typing import Any

from qsmlops.core.errors import DuplicateEntryError, IdentityError, NotFoundError
from qsmlops.database.engine import DatabaseEngine
from qsmlops.security.audit.events import AuditEvent
from qsmlops.security.identity.models import Identity


class BaseRepository:
    """Accepts either a raw DatabaseEngine or a DatabaseService."""

    def __init__(self, db) -> None:
        if hasattr(db, "ensure_ready"):
            db.ensure_ready()
            db = db.engine
        self._db: DatabaseEngine = db
        self._db.connect()


class AuditEventRepository(BaseRepository):
    def insert_mirror(self, event: AuditEvent, entry_hash: str) -> None:
        try:
            self._db.execute(
                """
                INSERT INTO audit_events
                    (event_id, timestamp, actor, action, resource, result,
                     evidence_reference, metadata, ledger_entry_hash)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    event.event_id,
                    event.timestamp,
                    event.actor,
                    event.action,
                    event.resource,
                    event.result,
                    event.evidence_reference,
                    json.dumps(event.metadata, sort_keys=True),
                    entry_hash,
                ),
            )
        except DuplicateEntryError:
            pass  # already mirrored (idempotent rebuilds)

    def fetch(self, event_id: str) -> AuditEvent | None:
        row = self._db.query_one(
            "SELECT * FROM audit_events WHERE event_id=?", (event_id,)
        )
        if row is None:
            return None
        event = AuditEvent(
            event_id=row["event_id"],
            timestamp=row["timestamp"],
            actor=row["actor"],
            action=row["action"],
            resource=row["resource"],
            result=row["result"],
            evidence_reference=row["evidence_reference"],
            metadata=json.loads(row["metadata"]),
        )
        return event

    def query(
        self,
        *,
        actor: str | None = None,
        action: str | None = None,
        resource: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        sql = "SELECT * FROM audit_events WHERE 1=1"
        params: list[Any] = []
        if actor:
            sql += " AND actor=?"
            params.append(actor)
        if action:
            sql += " AND action=?"
            params.append(action)
        if resource:
            sql += " AND resource=?"
            params.append(resource)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        rows = self._db.query_all(sql, params)
        return [
            AuditEvent(
                event_id=row["event_id"],
                timestamp=row["timestamp"],
                actor=row["actor"],
                action=row["action"],
                resource=row["resource"],
                result=row["result"],
                evidence_reference=row["evidence_reference"],
                metadata=json.loads(row["metadata"]),
            )
            for row in rows
        ]


class IdentityRepository(BaseRepository):
    """Persistence of identity records (queryable mirror of the TrustedObject)."""

    def insert(self, identity: Identity) -> None:
        try:
            self._db.execute(
                """
                INSERT INTO identities
                    (identity_id, kind, name, owner, role, status, description,
                     version, permissions, created_at, updated_at, hash,
                     signature, verification_status, metadata)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    identity.id,
                    identity.kind,
                    identity.name,
                    identity.owner,
                    identity.role,
                    identity.status,
                    identity.description,
                    identity.version,
                    json.dumps(sorted(identity.permissions)),
                    identity.created_at,
                    identity.updated_at,
                    identity.hash,
                    json.dumps(identity.signature, sort_keys=True),
                    identity.verification_status,
                    json.dumps(identity.metadata, sort_keys=True),
                ),
            )
        except DuplicateEntryError as exc:
            raise IdentityError(
                f"identity {identity.kind}:{identity.name} already exists"
            ) from exc

    def update(self, identity: Identity) -> None:
        self._db.execute(
            """
            UPDATE identities SET
                status=?, version=?, permissions=?, updated_at=?, hash=?,
                signature=?, verification_status=?, metadata=?, description=?
            WHERE identity_id=?
            """,
            (
                identity.status,
                identity.version,
                json.dumps(sorted(identity.permissions)),
                identity.updated_at,
                identity.hash,
                json.dumps(identity.signature, sort_keys=True),
                identity.verification_status,
                json.dumps(identity.metadata, sort_keys=True),
                identity.description,
                identity.id,
            ),
        )

    def get(self, identity_id: str) -> Identity | None:
        row = self._db.query_one(
            "SELECT * FROM identities WHERE identity_id=?", (identity_id,)
        )
        return self._row_to_identity(row) if row else None

    def find_by_name(self, kind: str, name: str) -> Identity | None:
        row = self._db.query_one(
            "SELECT * FROM identities WHERE kind=? AND name=?", (kind, name)
        )
        return self._row_to_identity(row) if row else None

    def list(self, kind: str | None = None, status: str | None = None) -> list[Identity]:
        sql = "SELECT * FROM identities WHERE 1=1"
        params: list[Any] = []
        if kind:
            sql += " AND kind=?"
            params.append(kind)
        if status:
            sql += " AND status=?"
            params.append(status)
        sql += " ORDER BY kind, name"
        return [self._row_to_identity(r) for r in self._db.query_all(sql, params)]

    def delete(self, identity_id: str) -> None:
        if self.get(identity_id) is None:
            raise NotFoundError(f"identity {identity_id} not found")
        self._db.execute("DELETE FROM identities WHERE identity_id=?", (identity_id,))

    @staticmethod
    def _row_to_identity(row: dict) -> Identity:
        return Identity.from_dict(
            {
                "object_type": "identity",
                "id": row["identity_id"],
                "kind": row["kind"],
                "name": row["name"],
                "owner": row["owner"],
                "role": row["role"],
                "status": row["status"],
                "description": row["description"],
                "version": row["version"],
                "permissions": json.loads(row["permissions"] or "[]"),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "hash": row["hash"],
                "signature": json.loads(row["signature"] or "null"),
                "verification_status": row["verification_status"],
                "metadata": json.loads(row["metadata"] or "{}"),
            }
        )
