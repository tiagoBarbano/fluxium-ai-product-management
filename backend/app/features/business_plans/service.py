from .domain.entities import BusinessPlan, BusinessPlanVersionConflict
from .repository import BusinessPlanRepository
from .schemas.requests import UpdateBusinessPlanRequest


class BusinessPlanNotFoundError(LookupError):
    pass


class BusinessPlanInitiativeNotFoundError(LookupError):
    pass


class BusinessPlanAccessError(PermissionError):
    pass


class BusinessPlanService:
    def __init__(self, repository: BusinessPlanRepository) -> None:
        self._repository = repository

    async def get(self, initiative_id: str, tenant_id: str, workspace_ids: set[str]) -> BusinessPlan:
        initiative = await self._get_initiative(tenant_id, initiative_id, workspace_ids)
        plan = await self._repository.find_by_initiative(tenant_id, workspace_ids, initiative.id)
        if plan is None:
            raise BusinessPlanNotFoundError("Business Plan not found")
        return plan

    async def update(
        self, initiative_id: str, request: UpdateBusinessPlanRequest, tenant_id: str, workspace_ids: set[str]
    ) -> BusinessPlan:
        initiative = await self._get_initiative(tenant_id, initiative_id, workspace_ids)
        plan = await self._repository.find_by_initiative(tenant_id, workspace_ids, initiative.id)
        changes = {
            field_name: value
            for field_name, value in request.model_dump(exclude={"expected_version"}).items()
            if value is not None
        }
        if plan is None:
            if request.expected_version != 0:
                raise BusinessPlanVersionConflict("A new Business Plan must use expected_version 0")
            if not changes.get("rationale"):
                raise ValueError("rationale is required when creating a Business Plan")
            plan = BusinessPlan.create(initiative_id=initiative.id, workspace_id=initiative.workspace_id, **changes)
            await self._repository.insert(tenant_id, plan)
            return plan
        plan.update(expected_version=request.expected_version, **changes)
        if not await self._repository.replace(tenant_id, plan, request.expected_version):
            raise BusinessPlanVersionConflict("Business Plan was modified by another request")
        return plan

    async def _get_initiative(self, tenant_id: str, initiative_id: str, workspace_ids: set[str]):
        initiative = await self._repository.find_initiative(tenant_id, initiative_id)
        if initiative is None:
            raise BusinessPlanInitiativeNotFoundError("Initiative not found")
        if initiative.workspace_id not in workspace_ids:
            raise BusinessPlanAccessError("Workspace access denied")
        return initiative