from fastapi import APIRouter, Depends, HTTPException, status

from ...database.mongo import get_database
from ...shared.auth import IdentityClaims, UserRole
from ...shared.auth.authorization import require_roles
from ...shared.auth.identity_repository import MongoIdentityRepository
from .repository import MongoWorkspaceRepository
from .schemas.requests import CreateWorkspaceRequest
from .schemas.responses import WorkspaceResponse
from .service import WorkspaceConflictError, WorkspaceService


router = APIRouter(prefix="/workspaces", tags=["workspaces"])
write_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR)


def get_workspace_service() -> WorkspaceService:
    database = get_database()
    return WorkspaceService(
        MongoWorkspaceRepository(database["workspaces"]),
        MongoIdentityRepository(
            users=database["identity_users"],
            consumers=database["identity_consumers"],
            refresh_tokens=database["identity_refresh_tokens"],
        ),
    )


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    request: CreateWorkspaceRequest,
    principal: IdentityClaims = Depends(write_roles),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    try:
        return WorkspaceResponse.from_entity(await service.create(request, principal))
    except WorkspaceConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc