from fastapi import APIRouter, Depends, HTTPException, Path

from ...database.mongo import get_database
from ...shared.auth import IdentityClaims, UserRole
from ...shared.auth.authorization import require_roles
from .domain.entities import BusinessPlanVersionConflict
from .repository import MongoBusinessPlanRepository
from .schemas.requests import UpdateBusinessPlanRequest
from .schemas.responses import BusinessPlanResponse
from .service import (
    BusinessPlanAccessError,
    BusinessPlanInitiativeNotFoundError,
    BusinessPlanNotFoundError,
    BusinessPlanService,
)


router = APIRouter(tags=["business-plans"])
write_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR)
read_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR, UserRole.VIEWER)


def get_business_plan_service() -> BusinessPlanService:
    database = get_database()
    return BusinessPlanService(MongoBusinessPlanRepository(database["business_plans"], database["initiatives"]))


@router.get("/initiatives/{initiative_id}/business-plan", response_model=BusinessPlanResponse)
async def get_business_plan(
    initiative_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: BusinessPlanService = Depends(get_business_plan_service),
) -> BusinessPlanResponse:
    try:
        return BusinessPlanResponse.from_entity(
            await service.get(initiative_id, principal.tenant_id, set(principal.workspace_ids))
        )
    except BusinessPlanInitiativeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BusinessPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BusinessPlanAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.patch("/initiatives/{initiative_id}/business-plan", response_model=BusinessPlanResponse)
async def update_business_plan(
    request: UpdateBusinessPlanRequest,
    initiative_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(write_roles),
    service: BusinessPlanService = Depends(get_business_plan_service),
) -> BusinessPlanResponse:
    try:
        return BusinessPlanResponse.from_entity(
            await service.update(initiative_id, request, principal.tenant_id, set(principal.workspace_ids))
        )
    except BusinessPlanInitiativeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BusinessPlanAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except BusinessPlanVersionConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc