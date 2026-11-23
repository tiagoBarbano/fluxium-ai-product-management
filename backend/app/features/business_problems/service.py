from ..opportunities.repository import OpportunityRepository
from .domain.entities import BusinessProblem, BusinessProblemVersionConflict
from .repository import BusinessProblemRepository
from .schemas.requests import CreateBusinessProblemRequest, UpdateBusinessProblemRequest


class BusinessProblemNotFoundError(LookupError):
    pass


class BusinessProblemAccessError(PermissionError):
    pass


class BusinessProblemOpportunityNotFoundError(LookupError):
    pass


class BusinessProblemService:
    def __init__(self, repository: BusinessProblemRepository, opportunities: OpportunityRepository) -> None:
        self._repository = repository
        self._opportunities = opportunities

    async def create(
        self,
        opportunity_id: str,
        request: CreateBusinessProblemRequest,
        tenant_id: str,
        subject: str,
        workspace_ids: set[str],
    ) -> BusinessProblem:
        opportunity = await self._opportunities.find_by_id(tenant_id, opportunity_id)
        self._check_opportunity(opportunity, workspace_ids)
        problem = BusinessProblem.create(
            workspace_id=opportunity.workspace_id or "",
            product_id=opportunity.product_id,
            opportunity_id=opportunity.id,
            description=request.description,
            audience=request.audience,
            reported_impact=request.reported_impact,
            estimated_impact=request.estimated_impact,
            created_by=subject,
        )
        await self._repository.insert(tenant_id, problem)
        return problem

    async def get(self, problem_id: str, tenant_id: str, workspace_ids: set[str]) -> BusinessProblem:
        problem = await self._repository.find_by_id(tenant_id, workspace_ids, problem_id)
        if problem is None:
            raise BusinessProblemNotFoundError("Business Problem not found")
        return problem

    async def update(
        self,
        problem_id: str,
        request: UpdateBusinessProblemRequest,
        tenant_id: str,
        workspace_ids: set[str],
    ) -> BusinessProblem:
        problem = await self.get(problem_id, tenant_id, workspace_ids)
        problem.update(
            expected_version=request.expected_version,
            description=request.description,
            audience=request.audience,
            reported_impact=request.reported_impact,
            estimated_impact=request.estimated_impact,
            status=request.status,
        )
        if not await self._repository.replace(tenant_id, problem, request.expected_version):
            raise BusinessProblemVersionConflict("Business Problem was modified by another request")
        return problem

    @staticmethod
    def _check_opportunity(opportunity: object | None, workspace_ids: set[str]) -> None:
        if opportunity is None:
            raise BusinessProblemOpportunityNotFoundError("Opportunity not found")
        if getattr(opportunity, "workspace_id", None) not in workspace_ids:
            raise BusinessProblemAccessError("Workspace access denied")