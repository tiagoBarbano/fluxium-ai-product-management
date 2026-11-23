from typing import Any

from .domain.entities import ReadinessAssessment, ReadinessDimensionScore
from .repository import ReadinessAssessmentRepository
from .schemas.requests import CreateReadinessAssessmentRequest


class ReadinessAssessmentNotFoundError(LookupError):
    pass


class ReadinessAssessmentAccessError(PermissionError):
    pass


class ReadinessInitiativeNotFoundError(LookupError):
    pass


class ReadinessAssessmentService:
    def __init__(self, repository: ReadinessAssessmentRepository) -> None:
        self._repository = repository

    async def create(
        self,
        initiative_id: str,
        request: CreateReadinessAssessmentRequest,
        tenant_id: str,
        workspace_ids: set[str] | frozenset[str],
        created_by: str,
        job_id: str | None = None,
        source_context: dict[str, Any] | None = None,
    ) -> ReadinessAssessment:
        initiative = await self._repository.find_initiative(tenant_id, initiative_id)
        if initiative is None:
            raise ReadinessInitiativeNotFoundError("Initiative not found")
        self._check_workspace(initiative.workspace_id, workspace_ids)
        assessment = ReadinessAssessment.create(
            initiative_id=initiative.id,
            workspace_id=initiative.workspace_id,
            dimensions=tuple(ReadinessDimensionScore(**dimension.model_dump()) for dimension in request.dimensions),
            missing_information=tuple(request.missing_information),
            open_questions=tuple(request.open_questions),
            confidence=request.confidence,
            context_version=request.context_version,
            provider=request.provider,
            model=request.model,
            prompt_version=request.prompt_version,
            created_by=created_by,
            source_context=source_context,
        )
        await self._repository.insert(tenant_id, assessment, job_id)
        return assessment

    async def find_id_by_job(
        self, job_id: str, tenant_id: str, workspace_ids: set[str] | frozenset[str]
    ) -> str | None:
        return await self._repository.find_id_by_job(tenant_id, set(workspace_ids), job_id)

    async def get_initiative_context(
        self, initiative_id: str, tenant_id: str, workspace_ids: set[str] | frozenset[str]
    ) -> dict[str, object]:
        initiative = await self._repository.find_initiative_context(tenant_id, initiative_id)
        if initiative is None:
            raise ReadinessInitiativeNotFoundError("Initiative not found")
        self._check_workspace(initiative.workspace_id, workspace_ids)
        return {
            "id": initiative.id, "workspace_id": initiative.workspace_id, "product_id": initiative.product_id,
            "opportunity_id": initiative.opportunity_id, "problem_id": initiative.problem_id,
            "title": initiative.title, "objective": initiative.objective,
            "hypothesis_ids": initiative.hypothesis_ids, "objective_ids": initiative.objective_ids,
            "evidence_ids": initiative.evidence_ids, "scope": initiative.scope,
            "out_of_scope": initiative.out_of_scope, "status": initiative.status, "version": initiative.version,
        }

    async def list_by_initiative(
        self, initiative_id: str, tenant_id: str, workspace_ids: set[str] | frozenset[str]
    ) -> list[ReadinessAssessment]:
        initiative = await self._repository.find_initiative(tenant_id, initiative_id)
        if initiative is None:
            raise ReadinessInitiativeNotFoundError("Initiative not found")
        self._check_workspace(initiative.workspace_id, workspace_ids)
        return await self._repository.list_by_initiative(tenant_id, set(workspace_ids), initiative_id)

    async def get(
        self, assessment_id: str, tenant_id: str, workspace_ids: set[str] | frozenset[str]
    ) -> ReadinessAssessment:
        assessment = await self._repository.find_by_id(tenant_id, set(workspace_ids), assessment_id)
        if assessment is None:
            raise ReadinessAssessmentNotFoundError("Readiness assessment not found")
        return assessment

    @staticmethod
    def _check_workspace(workspace_id: str, workspace_ids: set[str] | frozenset[str]) -> None:
        if workspace_id not in workspace_ids:
            raise ReadinessAssessmentAccessError("Workspace access denied")