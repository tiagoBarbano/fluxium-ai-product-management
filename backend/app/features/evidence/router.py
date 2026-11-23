from fastapi import APIRouter, Depends, HTTPException, Path, status

from ...database.mongo import get_database
from ...shared.auth import IdentityClaims, UserRole
from ...shared.auth.authorization import require_roles
from ..opportunities.repository import MongoOpportunityRepository
from .repository import (
    MongoEvidenceRepository,
    MongoHypothesisReferenceRepository,
    MongoProblemReferenceRepository,
)
from .schemas.requests import CreateEvidenceRequest
from .schemas.responses import EvidenceResponse
from .service import EvidenceAccessError, EvidenceReferenceError, EvidenceService


router = APIRouter(tags=["evidence"])
write_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR)
read_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR, UserRole.VIEWER)


def get_evidence_service() -> EvidenceService:
    database = get_database()
    return EvidenceService(
        MongoEvidenceRepository(database["evidence"]),
        MongoOpportunityRepository(database["opportunities"]),
        MongoProblemReferenceRepository(database["business_problems"]),
        MongoHypothesisReferenceRepository(database["hypotheses"]),
    )


@router.post("/business-problems/{problem_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def create_evidence(
    request: CreateEvidenceRequest,
    problem_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(write_roles),
    service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceResponse:
    request.problem_id = problem_id
    try:
        evidence = await service.create(
            "",
            request,
            principal.tenant_id,
            principal.workspace_ids,
            principal.subject,
        )
        return EvidenceResponse.from_entity(evidence)
    except EvidenceReferenceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EvidenceAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/business-problems/{problem_id}/evidence", response_model=list[EvidenceResponse])
async def list_evidence(
    problem_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: EvidenceService = Depends(get_evidence_service),
) -> list[EvidenceResponse]:
    try:
        evidence = await service.list_by_problem(problem_id, principal.tenant_id, principal.workspace_ids)
        return [EvidenceResponse.from_entity(item) for item in evidence]
    except EvidenceAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc