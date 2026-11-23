from fastapi import APIRouter, Depends, HTTPException, Path, Query

from ...database.mongo import get_database
from ...shared.auth import IdentityClaims, UserRole
from ...shared.auth.authorization import require_roles
from ...shared.audit.repository import MongoAuditRepository
from ...shared.audit.service import AuditService
from ..initiatives.repository import MongoInitiativeRepository
from ..readiness.repository import MongoReadinessAssessmentRepository
from .repository import MongoProposalRepository
from .schemas.requests import CreateProposalRequest, DecideProposalRequest
from .schemas.responses import ProposalResponse
from .domain.enums import ProposalStatus
from .service import ProposalAccessError, ProposalConflictError, ProposalNotFoundError, ProposalService


router = APIRouter(tags=["proposals"])
write_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR)
read_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR, UserRole.VIEWER)
approval_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER)


def get_proposal_service() -> ProposalService:
    database = get_database()
    return ProposalService(
        MongoProposalRepository(database["proposals"]),
        MongoInitiativeRepository(database["initiatives"]),
        MongoReadinessAssessmentRepository(database["assessments"], database["initiatives"]),
        AuditService(MongoAuditRepository(database["audit_events"])),
    )


@router.post("/proposals", response_model=ProposalResponse, status_code=201)
async def create_proposal(
    request: CreateProposalRequest,
    principal: IdentityClaims = Depends(write_roles),
    service: ProposalService = Depends(get_proposal_service),
) -> ProposalResponse:
    try:
        proposal = await service.create(request, principal.tenant_id, principal.workspace_ids, principal.subject)
        return ProposalResponse.from_entity(proposal)
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProposalAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/proposals", response_model=list[ProposalResponse])
async def list_proposals_by_status(
    status: ProposalStatus | None = Query(default=None),
    product_id: str | None = Query(default=None, min_length=1, max_length=100),
    opportunity_id: str | None = Query(default=None, min_length=1, max_length=100),
    initiative_id: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    principal: IdentityClaims = Depends(read_roles),
    service: ProposalService = Depends(get_proposal_service),
) -> list[ProposalResponse]:
    proposals = await service.list_filtered(
        principal.tenant_id,
        principal.workspace_ids,
        status,
        product_id,
        opportunity_id,
        initiative_id,
        limit,
    )
    return [ProposalResponse.from_entity(proposal) for proposal in proposals]


@router.get(
    "/initiatives/{initiative_id}/readiness-assessments/{assessment_id}/proposals",
    response_model=list[ProposalResponse],
)
async def list_proposals(
    initiative_id: str = Path(min_length=1, max_length=100),
    assessment_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: ProposalService = Depends(get_proposal_service),
) -> list[ProposalResponse]:
    try:
        proposals = await service.list_for_assessment(initiative_id, assessment_id, principal.tenant_id, principal.workspace_ids)
        return [ProposalResponse.from_entity(proposal) for proposal in proposals]
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProposalAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/initiatives/{initiative_id}/proposals", response_model=list[ProposalResponse])
async def list_initiative_proposals(
    initiative_id: str = Path(min_length=1, max_length=100),
    status: ProposalStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    principal: IdentityClaims = Depends(read_roles),
    service: ProposalService = Depends(get_proposal_service),
) -> list[ProposalResponse]:
    try:
        proposals = await service.list_for_initiative(
            initiative_id,
            principal.tenant_id,
            principal.workspace_ids,
            status,
            limit,
        )
        return [ProposalResponse.from_entity(proposal) for proposal in proposals]
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProposalAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/proposals/{proposal_id}/approve", response_model=ProposalResponse)
async def approve_proposal(
    request: DecideProposalRequest | None = None,
    proposal_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(approval_roles),
    service: ProposalService = Depends(get_proposal_service),
) -> ProposalResponse:
    try:
        proposal = await service.approve(
            proposal_id,
            principal.tenant_id,
            principal.workspace_ids,
            principal.subject,
            request.decision_reason if request else None,
        )
        return ProposalResponse.from_entity(proposal)
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProposalAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ProposalConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/proposals/{proposal_id}/reject", response_model=ProposalResponse)
async def reject_proposal(
    request: DecideProposalRequest,
    proposal_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(approval_roles),
    service: ProposalService = Depends(get_proposal_service),
) -> ProposalResponse:
    try:
        proposal = await service.reject(
            proposal_id,
            principal.tenant_id,
            principal.workspace_ids,
            principal.subject,
            request.decision_reason,
        )
        return ProposalResponse.from_entity(proposal)
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProposalAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ProposalConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc