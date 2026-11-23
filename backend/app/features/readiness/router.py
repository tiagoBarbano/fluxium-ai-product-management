from functools import lru_cache
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Path, status

from ...database.mongo import get_database
from ...shared.auth import IdentityClaims, UserRole
from ...shared.auth.authorization import require_roles
from ...shared.jobs import JobService, RedisJobStore
from ...shared.observability.request_context import get_correlation_id
from ..ai_gateway.providers.ollama import OllamaProvider
from ..ai_gateway.service import AIGatewayService
from .async_service import ReadinessAssessmentJobService
from .repository import MongoReadinessAssessmentRepository
from .schemas.async_requests import CreateReadinessAssessmentJobRequest
from .schemas.async_responses import ReadinessAssessmentJobResponse
from .schemas.requests import CreateReadinessAssessmentRequest
from .schemas.responses import ReadinessAssessmentResponse
from .service import (
    ReadinessAssessmentAccessError,
    ReadinessAssessmentNotFoundError,
    ReadinessAssessmentService,
    ReadinessInitiativeNotFoundError,
)


router = APIRouter(tags=["readiness"])
write_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR)
read_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR, UserRole.VIEWER)


def get_readiness_assessment_service() -> ReadinessAssessmentService:
    database = get_database()
    return ReadinessAssessmentService(
        MongoReadinessAssessmentRepository(database["assessments"], database["initiatives"])
    )


@lru_cache(maxsize=1)
def get_readiness_assessment_job_service() -> ReadinessAssessmentJobService:
    store = RedisJobStore.from_settings()
    return ReadinessAssessmentJobService(
        JobService(store), store, get_readiness_assessment_service(), AIGatewayService(OllamaProvider())
    )


@router.post(
    "/initiatives/{initiative_id}/readiness-assessment-jobs",
    response_model=ReadinessAssessmentJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_readiness_assessment_job(
    request: CreateReadinessAssessmentJobRequest,
    initiative_id: str = Path(min_length=1, max_length=100),
    idempotency_key: str = Header(alias="X-Idempotency-Key", min_length=1, max_length=200),
    correlation_id: str | None = Header(default=None, alias="Correlation-Id"),
    principal: IdentityClaims = Depends(write_roles),
    service: ReadinessAssessmentJobService = Depends(get_readiness_assessment_job_service),
) -> ReadinessAssessmentJobResponse:
    response = await service.submit(
        initiative_id,
        request,
        tenant_id=principal.tenant_id,
        workspace_ids=principal.workspace_ids,
        created_by=principal.subject,
        idempotency_key=f"{principal.tenant_id}:{idempotency_key}",
        correlation_id=correlation_id or get_correlation_id() or str(uuid4()),
    )
    return response


@router.get("/readiness-assessment-jobs/{job_id}", response_model=ReadinessAssessmentJobResponse)
async def get_readiness_assessment_job(
    job_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: ReadinessAssessmentJobService = Depends(get_readiness_assessment_job_service),
) -> ReadinessAssessmentJobResponse:
    try:
        response = await service.get_status(
            job_id,
            tenant_id=principal.tenant_id,
            workspace_ids=principal.workspace_ids,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return response


@router.post("/readiness-assessment-jobs/{job_id}/retry", response_model=ReadinessAssessmentJobResponse)
async def retry_readiness_assessment_job(
    job_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(write_roles),
    service: ReadinessAssessmentJobService = Depends(get_readiness_assessment_job_service),
) -> ReadinessAssessmentJobResponse:
    try:
        await service.get_status(
            job_id,
            tenant_id=principal.tenant_id,
            workspace_ids=principal.workspace_ids,
        )
        return await service.retry(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/initiatives/{initiative_id}/readiness-assessments",
    response_model=ReadinessAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_readiness_assessment(
    request: CreateReadinessAssessmentRequest,
    initiative_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(write_roles),
    service: ReadinessAssessmentService = Depends(get_readiness_assessment_service),
) -> ReadinessAssessmentResponse:
    try:
        assessment = await service.create(
            initiative_id, request, principal.tenant_id, principal.workspace_ids, principal.subject
        )
        return ReadinessAssessmentResponse.from_entity(assessment)
    except ReadinessInitiativeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadinessAssessmentAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/initiatives/{initiative_id}/readiness-assessments", response_model=list[ReadinessAssessmentResponse])
async def list_readiness_assessments(
    initiative_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: ReadinessAssessmentService = Depends(get_readiness_assessment_service),
) -> list[ReadinessAssessmentResponse]:
    try:
        assessments = await service.list_by_initiative(initiative_id, principal.tenant_id, principal.workspace_ids)
        return [ReadinessAssessmentResponse.from_entity(assessment) for assessment in assessments]
    except ReadinessInitiativeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadinessAssessmentAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/readiness-assessments/{assessment_id}", response_model=ReadinessAssessmentResponse)
async def get_readiness_assessment(
    assessment_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: ReadinessAssessmentService = Depends(get_readiness_assessment_service),
) -> ReadinessAssessmentResponse:
    try:
        assessment = await service.get(assessment_id, principal.tenant_id, principal.workspace_ids)
        return ReadinessAssessmentResponse.from_entity(assessment)
    except ReadinessAssessmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc