from fastapi import APIRouter, Depends, HTTPException, Query

from ...database.mongo import get_database
from ..auth import IdentityClaims, UserRole
from ..auth.authorization import require_roles
from .repository import MongoAuditRepository
from .schemas import AuditEventPage, AuditEventQuery
from .service import AuditService


router = APIRouter(tags=["audit"])
read_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR, UserRole.VIEWER)


def get_audit_service() -> AuditService:
    database = get_database()
    return AuditService(MongoAuditRepository(database["audit_events"]))


@router.get("/audit-events", response_model=AuditEventPage)
async def list_audit_events(
    workspace_id: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    resource: str | None = Query(default=None, min_length=1, max_length=100),
    resource_id: str | None = Query(default=None, min_length=1, max_length=100),
    initiative_id: str | None = Query(default=None, min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: AuditService = Depends(get_audit_service),
) -> AuditEventPage:
    if workspace_id not in principal.workspace_ids:
        raise HTTPException(status_code=403, detail="Workspace access denied")
    try:
        return await service.list_page(
            tenant_id=principal.tenant_id,
            workspace_id=workspace_id,
            query=AuditEventQuery(
                limit=limit,
                cursor=cursor,
                resource=resource,
                resource_id=resource_id,
                initiative_id=initiative_id,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc