from fastapi import APIRouter, Depends, HTTPException, Path, status

from ...database.mongo import get_database
from ...shared.auth import IdentityClaims, UserRole
from ...shared.auth.authorization import require_roles
from ..opportunities.repository import MongoOpportunityRepository
from .repository import MongoBusinessProblemRepository
from .schemas.requests import CreateBusinessProblemRequest, UpdateBusinessProblemRequest
from .schemas.responses import BusinessProblemResponse
from .service import (
    BusinessProblemAccessError,
    BusinessProblemNotFoundError,
    BusinessProblemOpportunityNotFoundError,
    BusinessProblemService,
)
from .domain.entities import BusinessProblemVersionConflict


router = APIRouter(tags=["business-problems"])
write_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR)
read_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR, UserRole.VIEWER)


def get_business_problem_service() -> BusinessProblemService:
    database = get_database()
    return BusinessProblemService(
        MongoBusinessProblemRepository(database["business_problems"]),
        MongoOpportunityRepository(database["opportunities"]),
    )


@router.post(
    "/opportunities/{opportunity_id}/business-problems",
    response_model=BusinessProblemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_business_problem(
    request: CreateBusinessProblemRequest,
    opportunity_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(write_roles),
    service: BusinessProblemService = Depends(get_business_problem_service),
) -> BusinessProblemResponse:
    try:
        problem = await service.create(
            opportunity_id,
            request,
            principal.tenant_id,
            principal.subject,
            principal.workspace_ids,
        )
        return BusinessProblemResponse.from_entity(problem)
    except BusinessProblemOpportunityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BusinessProblemAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/business-problems/{problem_id}", response_model=BusinessProblemResponse)
async def get_business_problem(
    problem_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: BusinessProblemService = Depends(get_business_problem_service),
) -> BusinessProblemResponse:
    try:
        problem = await service.get(problem_id, principal.tenant_id, principal.workspace_ids)
        return BusinessProblemResponse.from_entity(problem)
    except BusinessProblemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/business-problems/{problem_id}", response_model=BusinessProblemResponse)
async def update_business_problem(
    request: UpdateBusinessProblemRequest,
    problem_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(write_roles),
    service: BusinessProblemService = Depends(get_business_problem_service),
) -> BusinessProblemResponse:
    try:
        problem = await service.update(problem_id, request, principal.tenant_id, principal.workspace_ids)
        return BusinessProblemResponse.from_entity(problem)
    except BusinessProblemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BusinessProblemAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except BusinessProblemVersionConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc