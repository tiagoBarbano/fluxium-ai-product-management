from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from ...database.mongo import get_database
from ...shared.auth import IdentityClaims, UserRole
from ...shared.auth.authorization import require_roles
from ..products.repository import MongoProductRepository
from ..okrs.repository import MongoObjectiveRepository
from .repository import MongoOpportunityRepository
from .schemas.requests import CreateOpportunityRequest, UpdateOpportunityRequest
from .schemas.responses import OpportunityResponse
from .service import (
    OpportunityAccessError,
    OpportunityNotFoundError,
    OpportunityProductNotFoundError,
    OpportunityObjectiveNotFoundError,
    OpportunityService,
)


router = APIRouter(prefix="/opportunities", tags=["opportunities"])
write_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR)
read_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR, UserRole.VIEWER)


def get_opportunity_service() -> OpportunityService:
    database = get_database()
    return OpportunityService(
        MongoOpportunityRepository(database["opportunities"]),
        MongoProductRepository(database["products"]),
        MongoObjectiveRepository(database["objectives"]),
    )


@router.post("", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    request: CreateOpportunityRequest,
    principal: IdentityClaims = Depends(write_roles),
    service: OpportunityService = Depends(get_opportunity_service),
) -> OpportunityResponse:
    try:
        return await service.create(request, principal.tenant_id, principal.subject, principal.workspace_ids)
    except OpportunityProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OpportunityObjectiveNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OpportunityAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("", response_model=list[OpportunityResponse])
async def list_opportunities(
    workspace_id: str = Query(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: OpportunityService = Depends(get_opportunity_service),
) -> list[OpportunityResponse]:
    try:
        opportunities = await service.list(workspace_id, principal.tenant_id, principal.workspace_ids)
        return [OpportunityResponse.model_validate(opportunity) for opportunity in opportunities]
    except OpportunityAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: OpportunityService = Depends(get_opportunity_service),
) -> OpportunityResponse:
    try:
        return await service.get(opportunity_id, principal.tenant_id, principal.workspace_ids)
    except OpportunityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OpportunityAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.patch("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    request: UpdateOpportunityRequest,
    opportunity_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(write_roles),
    service: OpportunityService = Depends(get_opportunity_service),
) -> OpportunityResponse:
    try:
        return await service.update(opportunity_id, request, principal.tenant_id, principal.workspace_ids)
    except OpportunityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OpportunityProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OpportunityObjectiveNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OpportunityAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc