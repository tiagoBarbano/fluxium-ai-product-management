from ..business_problems.repository import BusinessProblemRepository
from ..okrs.repository import ObjectiveRepository
from ..opportunities.repository import OpportunityRepository
from ..products.repository import ProductRepository
from ..evidence.repository import HypothesisReferenceRepository
from .domain.entities import Initiative
from .repository import InitiativeRepository
from .schemas.requests import CreateInitiativeRequest, UpdateInitiativeRequest


class InitiativeNotFoundError(LookupError):
    pass


class InitiativeReferenceError(ValueError):
    pass


class InitiativeAccessError(PermissionError):
    pass


class InitiativeConflictError(ValueError):
    pass


class InitiativeService:
    def __init__(
        self,
        repository: InitiativeRepository,
        products: ProductRepository,
        opportunities: OpportunityRepository,
        problems: BusinessProblemRepository,
        hypotheses: HypothesisReferenceRepository,
        objectives: ObjectiveRepository,
    ) -> None:
        self._repository = repository
        self._products = products
        self._opportunities = opportunities
        self._problems = problems
        self._hypotheses = hypotheses
        self._objectives = objectives

    async def create(
        self,
        opportunity_id: str,
        request: CreateInitiativeRequest,
        tenant_id: str,
        workspace_ids: frozenset[str] | set[str],
        created_by: str,
    ) -> Initiative:
        opportunity = await self._opportunities.find_by_id(tenant_id, opportunity_id)
        workspace_id = self._validate_opportunity(opportunity, workspace_ids)
        product = await self._products.find_by_id(tenant_id, opportunity.product_id)
        self._validate_reference(product, workspace_id, "Product")
        if request.product_id is not None and request.product_id != product.id:
            raise InitiativeReferenceError("Product does not belong to the opportunity")
        await self._validate_references(request, tenant_id, workspace_id, opportunity)
        initiative = Initiative.create(
            workspace_id=workspace_id,
            product_id=product.id,
            opportunity_id=opportunity.id,
            title=request.title,
            objective=request.objective,
            scope=request.scope,
            created_by=created_by,
            problem_id=request.problem_id,
            hypothesis_ids=request.hypothesis_ids,
            objective_ids=request.objective_ids,
            evidence_ids=request.evidence_ids,
            out_of_scope=request.out_of_scope,
            readiness_score=request.readiness_score,
            readiness_confidence=request.readiness_confidence,
            delivery_confidence=request.delivery_confidence,
            outcome_confidence=request.outcome_confidence,
        )
        await self._repository.insert(tenant_id, initiative)
        return initiative

    async def get(self, initiative_id: str, tenant_id: str, workspace_ids: frozenset[str] | set[str]) -> Initiative:
        initiative = await self._repository.find_by_id(tenant_id, initiative_id)
        if initiative is None:
            raise InitiativeNotFoundError("Initiative not found")
        self._check_workspace(initiative.workspace_id, workspace_ids)
        return initiative

    async def list_by_product(self, product_id: str, tenant_id: str, workspace_ids: frozenset[str] | set[str]) -> list[Initiative]:
        product = await self._products.find_by_id(tenant_id, product_id)
        if product is None:
            raise InitiativeReferenceError("Product not found")
        self._check_workspace(product.workspace_id, workspace_ids)
        return await self._repository.list_by_product(tenant_id, product.workspace_id, product_id)

    async def update(
        self,
        initiative_id: str,
        request: UpdateInitiativeRequest,
        tenant_id: str,
        workspace_ids: frozenset[str] | set[str],
    ) -> Initiative:
        initiative = await self.get(initiative_id, tenant_id, workspace_ids)
        opportunity = await self._opportunities.find_by_id(tenant_id, initiative.opportunity_id)
        if opportunity is None or opportunity.workspace_id != initiative.workspace_id:
            raise InitiativeReferenceError("Opportunity not found")
        await self._validate_references(request, tenant_id, initiative.workspace_id, opportunity)
        try:
            initiative.update(
                expected_version=request.expected_version,
                **request.model_dump(exclude={"expected_version"}, exclude_none=True),
            )
        except ValueError as exc:
            raise InitiativeConflictError(str(exc)) from exc
        if not await self._repository.replace(tenant_id, initiative, request.expected_version):
            raise InitiativeConflictError("Initiative was updated by another request")
        return initiative

    async def _validate_references(self, request: object, tenant_id: str, workspace_id: str, opportunity: object) -> None:
        problem_id = getattr(request, "problem_id", None)
        if problem_id is not None:
            problem = await self._problems.find_by_id(tenant_id, {workspace_id}, problem_id)
            self._validate_reference(problem, workspace_id, "Business Problem")
            if problem.opportunity_id != opportunity.id or problem.product_id != opportunity.product_id:
                raise InitiativeReferenceError("Business Problem does not belong to the opportunity")
        for hypothesis_id in getattr(request, "hypothesis_ids", None) or []:
            hypothesis = await self._hypotheses.find_by_id(tenant_id, hypothesis_id)
            self._validate_reference(hypothesis, workspace_id, "Hypothesis")
            if getattr(hypothesis, "opportunity_id", None) != opportunity.id:
                raise InitiativeReferenceError("Hypothesis does not belong to the opportunity")
        for objective_id in getattr(request, "objective_ids", None) or []:
            objective = await self._objectives.find_by_id(tenant_id, objective_id)
            self._validate_reference(objective, workspace_id, "Objective")
            if getattr(objective, "product_id", None) != opportunity.product_id:
                raise InitiativeReferenceError("Objective does not belong to the product")

    @staticmethod
    def _validate_opportunity(opportunity: object | None, workspace_ids: frozenset[str] | set[str]) -> str:
        if opportunity is None:
            raise InitiativeReferenceError("Opportunity not found")
        workspace_id = getattr(opportunity, "workspace_id", None)
        InitiativeService._check_workspace(workspace_id, workspace_ids)
        return workspace_id

    @staticmethod
    def _validate_reference(reference: object | None, workspace_id: str, name: str) -> None:
        if reference is None:
            raise InitiativeReferenceError(f"{name} not found")
        if getattr(reference, "workspace_id", None) != workspace_id:
            raise InitiativeReferenceError(f"{name} does not belong to the initiative workspace")

    @staticmethod
    def _check_workspace(workspace_id: str | None, workspace_ids: frozenset[str] | set[str]) -> None:
        if workspace_id is None or workspace_id not in workspace_ids:
            raise InitiativeAccessError("Workspace access denied")