from __future__ import annotations

from uuid import uuid4

from ..products.repository import ProductRepository
from ..okrs.repository import ObjectiveRepository
from .domain.entities import Opportunity
from .domain.enums import OpportunityStatus
from .repository import OpportunityRepository
from .schemas.requests import CreateOpportunityRequest, UpdateOpportunityRequest


class OpportunityNotFoundError(LookupError):
    pass


class OpportunityAccessError(PermissionError):
    pass


class OpportunityProductNotFoundError(LookupError):
    pass


class OpportunityObjectiveNotFoundError(LookupError):
    pass


class OpportunityService:
    def __init__(self, repository: OpportunityRepository, products: ProductRepository, objectives: ObjectiveRepository) -> None:
        self._repository = repository
        self._products = products
        self._objectives = objectives

    async def create(
        self,
        request: CreateOpportunityRequest,
        tenant_id: str,
        subject: str,
        workspace_ids: set[str],
    ) -> Opportunity:
        product = await self._products.find_by_id(tenant_id, request.product_id)
        if product is None:
            raise OpportunityProductNotFoundError("Product not found")
        self._check_workspace(product.workspace_id, workspace_ids)
        await self._validate_objectives(request.objective_ids, tenant_id, product.workspace_id, product.id)
        opportunity = Opportunity(
            id=str(uuid4()),
            product_id=product.id,
            title=request.title,
            description=request.description,
            objective_ids=request.objective_ids,
            workspace_id=product.workspace_id,
            created_by=subject,
        )
        await self._repository.insert(tenant_id, opportunity)
        return opportunity

    async def get(self, opportunity_id: str, tenant_id: str, workspace_ids: set[str]) -> Opportunity:
        opportunity = await self._repository.find_by_id(tenant_id, opportunity_id)
        if opportunity is None:
            raise OpportunityNotFoundError("Opportunity not found")
        self._check_workspace(opportunity.workspace_id, workspace_ids)
        return opportunity

    async def list(self, workspace_id: str, tenant_id: str, workspace_ids: set[str]) -> list[Opportunity]:
        self._check_workspace(workspace_id, workspace_ids)
        return await self._repository.list_by_workspace(tenant_id, workspace_id)

    async def update(
        self,
        opportunity_id: str,
        request: UpdateOpportunityRequest,
        tenant_id: str,
        workspace_ids: set[str],
    ) -> Opportunity:
        opportunity = await self.get(opportunity_id, tenant_id, workspace_ids)
        if request.product_id is not None and request.product_id != opportunity.product_id:
            raise OpportunityAccessError("Opportunity Product cannot be changed after creation")
        if request.title is not None:
            opportunity.title = request.title
        if request.description is not None:
            opportunity.description = request.description
        if request.objective_ids is not None:
            product = await self._products.find_by_id(tenant_id, opportunity.product_id)
            if product is None:
                raise OpportunityProductNotFoundError("Product not found")
            await self._validate_objectives(request.objective_ids, tenant_id, opportunity.workspace_id, product.id)
            opportunity.objective_ids = request.objective_ids
        if request.status is not None:
            opportunity.transition_to(request.status)
        opportunity.touch()
        if not await self._repository.replace(tenant_id, opportunity, request.expected_version):
            raise ValueError("Opportunity was modified by another request")
        return opportunity

    @staticmethod
    def _check_workspace(workspace_id: str | None, workspace_ids: set[str]) -> None:
        if workspace_id is None or workspace_id not in workspace_ids:
            raise OpportunityAccessError("Workspace access denied")

    async def _validate_objectives(
        self,
        objective_ids: list[str],
        tenant_id: str,
        workspace_id: str | None,
        product_id: str,
    ) -> None:
        for objective_id in objective_ids:
            objective = await self._objectives.find_by_id(tenant_id, objective_id)
            if objective is None:
                raise OpportunityObjectiveNotFoundError("Objective not found")
            if objective.workspace_id != workspace_id:
                raise OpportunityAccessError("Objective workspace access denied")
            if objective.product_id != product_id:
                raise OpportunityAccessError("Objective product does not belong to the opportunity")