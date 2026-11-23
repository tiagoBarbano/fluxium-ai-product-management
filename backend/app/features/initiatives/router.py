from fastapi import APIRouter, Depends, HTTPException, Path, status

from ...database.mongo import get_database
from ...shared.auth import IdentityClaims, UserRole
from ...shared.auth.authorization import require_roles
from ..business_problems.repository import MongoBusinessProblemRepository
from ..evidence.repository import MongoHypothesisReferenceRepository
from ..okrs.repository import MongoObjectiveRepository
from ..opportunities.repository import MongoOpportunityRepository
from ..products.repository import MongoProductRepository
from .repository import MongoInitiativeRepository
from .schemas.requests import CreateInitiativeRequest, UpdateInitiativeRequest
from .schemas.responses import InitiativeResponse
from .service import InitiativeAccessError, InitiativeConflictError, InitiativeNotFoundError, InitiativeReferenceError, InitiativeService


router = APIRouter(tags=["initiatives"])
write_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR)
read_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR, UserRole.VIEWER)


def get_initiative_service() -> InitiativeService:
    database = get_database()
    return InitiativeService(
        MongoInitiativeRepository(database["initiatives"]),
        MongoProductRepository(database["products"]),
        MongoOpportunityRepository(database["opportunities"]),
        MongoBusinessProblemRepository(database["business_problems"]),
        MongoHypothesisReferenceRepository(database["hypotheses"]),
        MongoObjectiveRepository(database["objectives"]),
    )


@router.post("/opportunities/{opportunity_id}/initiatives", response_model=InitiativeResponse, status_code=status.HTTP_201_CREATED)
async def create_initiative(
    request: CreateInitiativeRequest,
    opportunity_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(write_roles),
    service: InitiativeService = Depends(get_initiative_service),
) -> InitiativeResponse:
    try:
        return InitiativeResponse.from_entity(await service.create(opportunity_id, request, principal.tenant_id, principal.workspace_ids, principal.subject))
    except InitiativeReferenceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InitiativeAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/initiatives/{initiative_id}", response_model=InitiativeResponse)
async def get_initiative(
    initiative_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: InitiativeService = Depends(get_initiative_service),
) -> InitiativeResponse:
    try:
        return InitiativeResponse.from_entity(await service.get(initiative_id, principal.tenant_id, principal.workspace_ids))
    except InitiativeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InitiativeAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/products/{product_id}/initiatives", response_model=list[InitiativeResponse])
async def list_product_initiatives(
    product_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: InitiativeService = Depends(get_initiative_service),
) -> list[InitiativeResponse]:
    try:
        return [InitiativeResponse.from_entity(item) for item in await service.list_by_product(product_id, principal.tenant_id, principal.workspace_ids)]
    except InitiativeReferenceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InitiativeAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.patch("/initiatives/{initiative_id}", response_model=InitiativeResponse)
async def update_initiative(
    request: UpdateInitiativeRequest,
    initiative_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(write_roles),
    service: InitiativeService = Depends(get_initiative_service),
) -> InitiativeResponse:
    try:
        return InitiativeResponse.from_entity(await service.update(initiative_id, request, principal.tenant_id, principal.workspace_ids))
    except InitiativeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InitiativeReferenceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InitiativeAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InitiativeConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc