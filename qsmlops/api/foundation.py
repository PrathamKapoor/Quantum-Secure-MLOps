"""Foundation API: platform status, identity and audit endpoints.

These are Part-1 foundation endpoints. ML lifecycle APIs already exist in
``qsmlops.api.app`` (dashboard routes); nothing here duplicates them.

Endpoints:
    GET /health
    GET /system/info
    GET /status
    GET /identity
    POST /identity
    GET /identity/{identity_id}
    GET /audit
    GET /audit/verify
"""
from __future__ import annotations

import time

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from qsmlops import __version__
from qsmlops.core.errors import (
    IdentityAlreadyExistsError,
    IdentityError,
    NotFoundError,
    PermissionDeniedError,
    QSMLOPSError,
)
from qsmlops.core.logging import get_logger
from qsmlops.security.audit.events import AuditEvent
from qsmlops.security.identity.models import IDENTITY_KINDS

log = get_logger(__name__)


class CreateIdentityRequest(BaseModel):
    kind: str = Field(..., description="human | service | agent")
    name: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)
    role: str = Field(default="", description="permission model role name")
    permissions: list[str] = Field(default_factory=list)
    description: str = ""


def _identity_summary(identity) -> dict:
    return {
        "id": identity.id,
        "kind": identity.kind,
        "name": identity.name,
        "owner": identity.owner,
        "role": identity.role,
        "permissions": sorted(identity.permissions),
        "status": identity.status,
        "version": identity.version,
        "verification_status": identity.verification_status,
        "created_at": identity.created_at,
        "updated_at": identity.updated_at,
    }


def register_foundation_routes(
    app: FastAPI,
    *,
    settings,
    identity_service,
    audit_service,
    container=None,
    started_at: float | None = None,
) -> None:
    """Attach the Part-1 foundation endpoints to an application."""
    app_started_at = started_at if started_at is not None else time.time()

    @app.exception_handler(QSMLOPSError)
    async def _platform_error_handler(request: Request, exc: QSMLOPSError):
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=getattr(exc, "status_code", 500),
            content={"error": exc.code, "detail": str(exc)},
        )

    # -------------------- health / status --------------------
    @app.get("/health")
    def health() -> dict:
        chain_ok, message = audit_service.verify()
        return {
            "status": "ok" if chain_ok else "degraded",
            "version": __version__,
            "checks": {
                "audit_ledger": {"ok": chain_ok, "message": message},
            },
        }

    @app.get("/system/info")
    def system_info() -> dict:
        return {
            "name": "Quantum-Secure Agentic MLOps Pipeline Management System",
            "package": "qsmlops",
            "version": __version__,
            "environment": settings.env,
            "settings_summary": settings.summary(),
        }

    @app.get("/status")
    def status() -> dict:
        chain_ok, message = audit_service.verify()
        identities = identity_service.list()
        registry = container.get("registry") if container is not None else None
        model_versions = registry.list_versions() if registry is not None else []
        active_deployments = []
        if registry is not None:
            for name in sorted({v["model_name"] for v in model_versions}):
                active = registry.active_deployment(name)
                if active:
                    active_deployments.append(
                        {"model": name, "version_id": active["version_id"]}
                    )
        return {
            "status": "ok",
            "started_at": app_started_at,
            "environment": settings.env,
            "audit": {"chain_ok": chain_ok, "message": message},
            "identities": {
                "total": len(identities),
                "active": sum(1 for i in identities if i.is_active()),
            },
            "models": {
                "versions": len(model_versions),
                "active_deployments": len(active_deployments),
            },
        }

    # -------------------- identity --------------------
    @app.get("/identity")
    def list_identities(kind: str | None = None, status: str | None = None) -> dict:
        if kind is not None and kind not in IDENTITY_KINDS:
            raise HTTPException(status_code=422, detail=f"invalid kind {kind!r}")
        identities = identity_service.list(kind=kind, status=status)
        return {"identities": [_identity_summary(i) for i in identities]}

    @app.post("/identity", status_code=201)
    def create_identity(payload: CreateIdentityRequest) -> dict:
        try:
            identity = identity_service.create_identity(
                kind=payload.kind,
                name=payload.name,
                owner=payload.owner,
                role=payload.role,
                permissions=set(payload.permissions),
                description=payload.description,
            )
        except IdentityAlreadyExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except IdentityError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except PermissionDeniedError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return {"identity": _identity_summary(identity)}

    @app.get("/identity/{identity_id}")
    def get_identity(identity_id: str) -> dict:
        try:
            identity = identity_service.get(identity_id)
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"identity": _identity_summary(identity)}

    # -------------------- audit --------------------
    @app.get("/audit")
    def list_audit_events(
        actor: str | None = None,
        action: str | None = None,
        resource: str | None = None,
        limit: int = 100,
    ) -> dict:
        events = audit_service.query(
            actor=actor, action=action, resource=resource, limit=max(1, min(limit, 1000))
        )
        return {"events": [e.to_dict() for e in events], "count": len(events)}

    @app.get("/audit/verify")
    def verify_audit() -> dict:
        ok, message = audit_service.verify()
        return {"chain_ok": ok, "message": message, "head": audit_service.head()}
