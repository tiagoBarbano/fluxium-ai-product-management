from ..opportunities.repository import OpportunityRepository
from .domain.entities import Evidence
from .repository import EvidenceRepository, HypothesisReferenceRepository, ProblemReferenceRepository
from .schemas.requests import CreateEvidenceRequest


class EvidenceNotFoundError(LookupError):
    pass


class EvidenceReferenceError(ValueError):
    pass


class EvidenceAccessError(PermissionError):
    pass


class EvidenceService:
    def __init__(
        self,
        repository: EvidenceRepository,
        opportunities: OpportunityRepository,
        problems: ProblemReferenceRepository | None = None,
        hypotheses: HypothesisReferenceRepository | None = None,
    ) -> None:
        self._repository = repository
        self._opportunities = opportunities
        self._problems = problems
        self._hypotheses = hypotheses

    async def create(
        self,
        opportunity_id: str,
        request: CreateEvidenceRequest,
        tenant_id: str,
        workspace_ids: frozenset[str] | set[str],
        created_by: str,
    ) -> Evidence:
        if not opportunity_id and request.problem_id is not None and self._problems is not None:
            problem = await self._problems.find_by_id(tenant_id, request.problem_id)
            if problem is not None:
                opportunity_id = getattr(problem, "opportunity_id", "")
        opportunity = await self._opportunities.find_by_id(tenant_id, opportunity_id)
        if opportunity is None:
            raise EvidenceReferenceError("Opportunity not found")
        workspace_id = getattr(opportunity, "workspace_id", None)
        self._check_workspace(workspace_id, workspace_ids)
        if request.problem_id is not None:
            await self._validate_reference(self._problems, tenant_id, request.problem_id, workspace_id, opportunity_id, "Problem")
        if request.hypothesis_id is not None:
            await self._validate_reference(self._hypotheses, tenant_id, request.hypothesis_id, workspace_id, opportunity_id, "Hypothesis")
        evidence = Evidence.create(
            workspace_id=workspace_id,
            opportunity_id=opportunity_id,
            problem_id=request.problem_id,
            hypothesis_id=request.hypothesis_id,
            evidence_type=request.type,
            origin=request.origin,
            description=request.description,
            source=request.source,
            reference=request.reference,
            created_by=created_by,
        )
        await self._repository.insert(tenant_id, evidence)
        return evidence

    async def list_by_problem(
        self, problem_id: str, tenant_id: str, workspace_ids: frozenset[str] | set[str]
    ) -> list[Evidence]:
        if self._problems is None:
            raise EvidenceReferenceError("Problem validation is not configured")
        problem = await self._problems.find_by_id(tenant_id, problem_id)
        if problem is None:
            raise EvidenceReferenceError("Problem not found")
        workspace_id = getattr(problem, "workspace_id", None)
        self._check_workspace(workspace_id, workspace_ids)
        return await self._repository.list_by_problem(tenant_id, workspace_id, problem_id)

    async def _validate_reference(
        self, repository: object | None, tenant_id: str, reference_id: str, workspace_id: str, opportunity_id: str, label: str
    ) -> None:
        if repository is None:
            raise EvidenceReferenceError(f"{label} validation is not configured")
        reference = await repository.find_by_id(tenant_id, reference_id)
        if reference is None or getattr(reference, "workspace_id", None) != workspace_id or getattr(reference, "opportunity_id", None) != opportunity_id:
            raise EvidenceReferenceError(f"{label} does not belong to the opportunity workspace")

    @staticmethod
    def _check_workspace(workspace_id: str | None, workspace_ids: frozenset[str] | set[str]) -> None:
        if workspace_id is None or workspace_id not in workspace_ids:
            raise EvidenceAccessError("Workspace access denied")