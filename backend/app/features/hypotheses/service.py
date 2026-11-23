from __future__ import annotations

from ..evidence.repository import EvidenceRepository
from ..opportunities.repository import OpportunityRepository
from .domain.entities import Hypothesis
from .repository import HypothesisRepository
from .schemas.requests import CreateHypothesisRequest, UpdateHypothesisRequest


class HypothesisNotFoundError(LookupError):
    pass


class HypothesisReferenceError(ValueError):
    pass


class HypothesisAccessError(PermissionError):
    pass


class HypothesisConflictError(ValueError):
    pass


class HypothesisService:
    def __init__(self, repository: HypothesisRepository, opportunities: OpportunityRepository, evidence: EvidenceRepository) -> None:
        self._repository = repository
        self._opportunities = opportunities
        self._evidence = evidence

    async def create(self, opportunity_id: str, request: CreateHypothesisRequest, tenant_id: str, workspace_ids: frozenset[str] | set[str], created_by: str) -> Hypothesis:
        opportunity = await self._opportunities.find_by_id(tenant_id, opportunity_id)
        if opportunity is None:
            raise HypothesisReferenceError("Opportunity not found")
        workspace_id = getattr(opportunity, "workspace_id", None)
        self._check_workspace(workspace_id, workspace_ids)
        await self._validate_evidence(request.evidence_ids, tenant_id, workspace_id, opportunity_id)
        hypothesis = Hypothesis.create(
            workspace_id=workspace_id, opportunity_id=opportunity_id, statement=request.statement,
            expected_behavior=request.expected_behavior, expected_outcome=request.expected_outcome,
            evidence_ids=request.evidence_ids, confidence=request.confidence, created_by=created_by,
        )
        await self._repository.insert(tenant_id, hypothesis)
        return hypothesis

    async def list(self, opportunity_id: str, tenant_id: str, workspace_ids: frozenset[str] | set[str]) -> list[Hypothesis]:
        opportunity = await self._get_opportunity(opportunity_id, tenant_id, workspace_ids)
        return await self._repository.list_by_opportunity(tenant_id, opportunity.workspace_id, opportunity_id)

    async def get(self, hypothesis_id: str, tenant_id: str, workspace_ids: frozenset[str] | set[str]) -> Hypothesis:
        hypothesis = await self._repository.find_by_id(tenant_id, hypothesis_id)
        if hypothesis is None:
            raise HypothesisNotFoundError("Hypothesis not found")
        self._check_workspace(hypothesis.workspace_id, workspace_ids)
        return hypothesis

    async def update(self, hypothesis_id: str, request: UpdateHypothesisRequest, tenant_id: str, workspace_ids: frozenset[str] | set[str]) -> Hypothesis:
        hypothesis = await self.get(hypothesis_id, tenant_id, workspace_ids)
        if request.evidence_ids is not None:
            await self._validate_evidence(request.evidence_ids, tenant_id, hypothesis.workspace_id, hypothesis.opportunity_id)
        try:
            hypothesis.update(expected_version=request.expected_version, **request.model_dump(exclude={"expected_version"}, exclude_none=True))
        except ValueError as exc:
            raise HypothesisConflictError(str(exc)) from exc
        if not await self._repository.replace(tenant_id, hypothesis, request.expected_version):
            raise HypothesisConflictError("Hypothesis was updated by another request")
        return hypothesis

    async def _get_opportunity(self, opportunity_id: str, tenant_id: str, workspace_ids: frozenset[str] | set[str]):
        opportunity = await self._opportunities.find_by_id(tenant_id, opportunity_id)
        if opportunity is None:
            raise HypothesisReferenceError("Opportunity not found")
        self._check_workspace(getattr(opportunity, "workspace_id", None), workspace_ids)
        return opportunity

    async def _validate_evidence(self, evidence_ids: list[str], tenant_id: str, workspace_id: str, opportunity_id: str) -> None:
        for evidence_id in evidence_ids:
            evidence = await self._evidence.find_by_id(tenant_id, evidence_id)
            if evidence is None or evidence.workspace_id != workspace_id or evidence.opportunity_id != opportunity_id:
                raise HypothesisReferenceError("Evidence does not belong to the opportunity workspace")

    @staticmethod
    def _check_workspace(workspace_id: str | None, workspace_ids: frozenset[str] | set[str]) -> None:
        if workspace_id is None or workspace_id not in workspace_ids:
            raise HypothesisAccessError("Workspace access denied")