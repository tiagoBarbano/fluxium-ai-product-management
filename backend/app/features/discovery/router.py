from fastapi import APIRouter, Depends, HTTPException, Path, status

from ...database.mongo import get_database
from ...shared.auth import IdentityClaims, UserRole
from ...shared.auth.authorization import require_roles
from ..opportunities.repository import MongoOpportunityRepository
from .repository import MongoDiscoveryRepository
from .schemas.requests import CreateDiscoveryMessageRequest, UpdateDiscoveryContextRequest
from .schemas.responses import DiscoveryMessageResponse, DiscoverySessionResponse
from .service import DiscoveryAccessError, DiscoveryConflictError, DiscoveryNotFoundError, DiscoveryService


router = APIRouter(tags=["discovery"])
roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR)


def get_discovery_service() -> DiscoveryService:
    database = get_database()
    return DiscoveryService(
        MongoDiscoveryRepository(database["discovery_sessions"], database["discovery_messages"]),
        MongoOpportunityRepository(database["opportunities"]),
    )


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, DiscoveryNotFoundError): return HTTPException(404, str(exc))
    if isinstance(exc, DiscoveryAccessError): return HTTPException(403, str(exc))
    return HTTPException(409, str(exc))


@router.post("/opportunities/{opportunity_id}/discovery-sessions", response_model=DiscoverySessionResponse, status_code=status.HTTP_201_CREATED)
async def start_discovery(opportunity_id: str = Path(min_length=1, max_length=100), principal: IdentityClaims = Depends(roles), service: DiscoveryService = Depends(get_discovery_service)) -> DiscoverySessionResponse:
    try:
        session = await service.start(opportunity_id, principal.tenant_id, principal.subject, principal.workspace_ids)
        return DiscoverySessionResponse.model_validate(session)
    except (DiscoveryNotFoundError, DiscoveryAccessError, DiscoveryConflictError) as exc:
        raise _error(exc) from exc


@router.get("/discovery-sessions/{session_id}", response_model=DiscoverySessionResponse)
async def get_discovery(session_id: str = Path(min_length=1, max_length=100), principal: IdentityClaims = Depends(roles), service: DiscoveryService = Depends(get_discovery_service)) -> DiscoverySessionResponse:
    try:
        session, messages = await service.get(session_id, principal.tenant_id, principal.workspace_ids)
        return DiscoverySessionResponse.model_validate({"id": session.id, "opportunity_id": session.opportunity_id, "workspace_id": session.workspace_id, "status": session.status, "mode": session.mode, "context": session.context, "version": session.version, "created_by": session.created_by, "created_at": session.created_at, "updated_at": session.updated_at, "messages": messages})
    except (DiscoveryNotFoundError, DiscoveryAccessError) as exc:
        raise _error(exc) from exc


@router.post("/discovery-sessions/{session_id}/messages", response_model=DiscoveryMessageResponse, status_code=status.HTTP_201_CREATED)
async def add_discovery_message(request: CreateDiscoveryMessageRequest, session_id: str = Path(min_length=1, max_length=100), principal: IdentityClaims = Depends(roles), service: DiscoveryService = Depends(get_discovery_service)) -> DiscoveryMessageResponse:
    try:
        return await service.add_message(session_id, request, principal.tenant_id, principal.subject, principal.workspace_ids)
    except (DiscoveryNotFoundError, DiscoveryAccessError, DiscoveryConflictError) as exc:
        raise _error(exc) from exc


@router.patch("/discovery-sessions/{session_id}/context", response_model=DiscoverySessionResponse)
async def update_discovery_context(request: UpdateDiscoveryContextRequest, session_id: str = Path(min_length=1, max_length=100), principal: IdentityClaims = Depends(roles), service: DiscoveryService = Depends(get_discovery_service)) -> DiscoverySessionResponse:
    try:
        session = await service.update_context(session_id, request, principal.tenant_id, principal.workspace_ids)
        return DiscoverySessionResponse.model_validate(session)
    except (DiscoveryNotFoundError, DiscoveryAccessError, DiscoveryConflictError, ValueError) as exc:
        raise _error(exc) from exc


@router.post("/discovery-sessions/{session_id}/complete", response_model=DiscoverySessionResponse)
async def complete_discovery(session_id: str = Path(min_length=1, max_length=100), principal: IdentityClaims = Depends(roles), service: DiscoveryService = Depends(get_discovery_service)) -> DiscoverySessionResponse:
    try:
        session = await service.complete(session_id, principal.tenant_id, principal.workspace_ids)
        return DiscoverySessionResponse.model_validate(session)
    except (DiscoveryNotFoundError, DiscoveryAccessError, DiscoveryConflictError, ValueError) as exc:
        raise _error(exc) from exc