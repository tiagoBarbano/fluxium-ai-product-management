from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from ...database.mongo import get_database
from ...shared.auth import IdentityClaims, UserRole
from ...shared.auth.authorization import require_roles
from ..products.repository import MongoProductRepository
from .repository import MongoObjectiveRepository
from .schemas.requests import CreateObjectiveRequest, UpdateObjectiveRequest
from .schemas.responses import ObjectiveResponse
from .service import ObjectiveAccessError, ObjectiveNotFoundError, ObjectiveReferenceError, ObjectiveService


router = APIRouter(prefix="/objectives", tags=["okrs"])
write_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR)
read_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR, UserRole.VIEWER)


def get_objective_service() -> ObjectiveService:
    database = get_database()
    return ObjectiveService(
        MongoObjectiveRepository(database["objectives"]),
        MongoProductRepository(database["products"]),
    )


@router.post("", response_model=ObjectiveResponse, status_code=status.HTTP_201_CREATED)
async def create_objective(
    request: CreateObjectiveRequest,
    workspace_id: str = Query(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(write_roles),
    service: ObjectiveService = Depends(get_objective_service),
) -> ObjectiveResponse:
    try:
        return await service.create(request, principal.tenant_id, workspace_id, principal.workspace_ids)
    except ObjectiveAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ObjectiveReferenceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[ObjectiveResponse])
async def list_objectives(
    workspace_id: str = Query(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: ObjectiveService = Depends(get_objective_service),
) -> list[ObjectiveResponse]:
    try:
        objectives = await service.list(workspace_id, principal.tenant_id, principal.workspace_ids)
        return [ObjectiveResponse.model_validate(objective) for objective in objectives]
    except ObjectiveAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/{objective_id}", response_model=ObjectiveResponse)
async def get_objective(
    objective_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: ObjectiveService = Depends(get_objective_service),
) -> ObjectiveResponse:
    try:
        return await service.get(objective_id, principal.tenant_id, principal.workspace_ids)
    except ObjectiveNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ObjectiveAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.patch("/{objective_id}", response_model=ObjectiveResponse)
async def update_objective(
    request: UpdateObjectiveRequest,
    objective_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(write_roles),
    service: ObjectiveService = Depends(get_objective_service),
) -> ObjectiveResponse:
    try:
        return await service.update(objective_id, request, principal.tenant_id, principal.workspace_ids)
    except ObjectiveNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ObjectiveAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc