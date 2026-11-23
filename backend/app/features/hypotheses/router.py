from fastapi import APIRouter, Depends, HTTPException, Path, status

from ...database.mongo import get_database
from ...shared.auth import IdentityClaims, UserRole
from ...shared.auth.authorization import require_roles
from ..evidence.repository import MongoEvidenceRepository
from ..opportunities.repository import MongoOpportunityRepository
from .repository import MongoHypothesisRepository
from .schemas.requests import CreateHypothesisRequest, UpdateHypothesisRequest
from .schemas.responses import HypothesisResponse
from .service import HypothesisAccessError, HypothesisConflictError, HypothesisNotFoundError, HypothesisReferenceError, HypothesisService


router = APIRouter(tags=["hypotheses"])
write_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR)
read_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR, UserRole.VIEWER)


def get_hypothesis_service() -> HypothesisService:
    database = get_database()
    return HypothesisService(MongoHypothesisRepository(database["hypotheses"]), MongoOpportunityRepository(database["opportunities"]), MongoEvidenceRepository(database["evidence"]))


@router.post("/opportunities/{opportunity_id}/hypotheses", response_model=HypothesisResponse, status_code=status.HTTP_201_CREATED)
async def create_hypothesis(request: CreateHypothesisRequest, opportunity_id: str = Path(min_length=1, max_length=100), principal: IdentityClaims = Depends(write_roles), service: HypothesisService = Depends(get_hypothesis_service)) -> HypothesisResponse:
    try:
        return HypothesisResponse.from_entity(await service.create(opportunity_id, request, principal.tenant_id, principal.workspace_ids, principal.subject))
    except HypothesisReferenceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HypothesisAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/opportunities/{opportunity_id}/hypotheses", response_model=list[HypothesisResponse])
async def list_hypotheses(opportunity_id: str = Path(min_length=1, max_length=100), principal: IdentityClaims = Depends(read_roles), service: HypothesisService = Depends(get_hypothesis_service)) -> list[HypothesisResponse]:
    try:
        return [HypothesisResponse.from_entity(item) for item in await service.list(opportunity_id, principal.tenant_id, principal.workspace_ids)]
    except HypothesisReferenceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HypothesisAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/hypotheses/{hypothesis_id}", response_model=HypothesisResponse)
async def get_hypothesis(hypothesis_id: str = Path(min_length=1, max_length=100), principal: IdentityClaims = Depends(read_roles), service: HypothesisService = Depends(get_hypothesis_service)) -> HypothesisResponse:
    try:
        return HypothesisResponse.from_entity(await service.get(hypothesis_id, principal.tenant_id, principal.workspace_ids))
    except HypothesisNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HypothesisAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.patch("/hypotheses/{hypothesis_id}", response_model=HypothesisResponse)
async def update_hypothesis(request: UpdateHypothesisRequest, hypothesis_id: str = Path(min_length=1, max_length=100), principal: IdentityClaims = Depends(write_roles), service: HypothesisService = Depends(get_hypothesis_service)) -> HypothesisResponse:
    try:
        return HypothesisResponse.from_entity(await service.update(hypothesis_id, request, principal.tenant_id, principal.workspace_ids))
    except HypothesisNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HypothesisAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except HypothesisConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc