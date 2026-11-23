from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from ..products.repository import ProductRepository
from .domain.entities import KeyResult, Objective
from .repository import ObjectiveRepository
from .schemas.requests import CreateObjectiveRequest, UpdateKeyResultRequest, UpdateObjectiveRequest


class ObjectiveNotFoundError(LookupError):
    pass


class ObjectiveAccessError(PermissionError):
    pass


class ObjectiveReferenceError(ValueError):
    pass


class ObjectiveService:
    def __init__(
        self,
        repository: ObjectiveRepository,
        products: ProductRepository,
    ) -> None:
        self._repository = repository
        self._products = products

    async def create(
        self,
        request: CreateObjectiveRequest,
        tenant_id: str,
        workspace_id: str,
        workspace_ids: set[str],
    ) -> Objective:
        self._check_workspace(workspace_id, workspace_ids)
        await self._validate_product(request.product_id, tenant_id, workspace_id)
        objective = Objective(
            id=str(uuid4()),
            title=request.title,
            description=request.description,
            key_results=[KeyResult(**result.model_dump()) for result in request.key_results],
            product_id=request.product_id,
            workspace_id=workspace_id,
        )
        await self._repository.insert(tenant_id, objective)
        return objective

    async def _validate_product(self, product_id: str, tenant_id: str, workspace_id: str) -> None:
        product = await self._products.find_by_id(tenant_id, product_id)
        self._validate_reference(product, workspace_id, "Product")

    async def get(self, objective_id: str, tenant_id: str, workspace_ids: set[str]) -> Objective:
        objective = await self._repository.find_by_id(tenant_id, objective_id)
        if objective is None:
            raise ObjectiveNotFoundError("Objective not found")
        self._check_workspace(objective.workspace_id, workspace_ids)
        return objective

    async def list(self, workspace_id: str, tenant_id: str, workspace_ids: set[str]) -> list[Objective]:
        self._check_workspace(workspace_id, workspace_ids)
        return await self._repository.list_by_workspace(tenant_id, workspace_id)

    async def update(
        self,
        objective_id: str,
        request: UpdateObjectiveRequest,
        tenant_id: str,
        workspace_ids: set[str],
    ) -> Objective:
        objective = await self.get(objective_id, tenant_id, workspace_ids)
        if request.title is not None:
            objective.title = request.title
        if request.description is not None:
            objective.description = request.description
        if request.key_results is not None:
            objective.key_results = self._replace_key_results(objective.key_results, request.key_results)
        objective.updated_at = datetime.now(timezone.utc)
        await self._repository.replace(tenant_id, objective)
        return objective

    @staticmethod
    def _check_workspace(workspace_id: str | None, workspace_ids: set[str]) -> None:
        if workspace_id is None or workspace_id not in workspace_ids:
            raise ObjectiveAccessError("Workspace access denied")

    @staticmethod
    def _validate_reference(reference: object | None, workspace_id: str, name: str) -> None:
        if reference is None:
            raise ObjectiveReferenceError(f"{name} not found")
        if getattr(reference, "workspace_id", None) != workspace_id:
            raise ObjectiveAccessError(f"{name} workspace access denied")

    @staticmethod
    def _replace_key_results(
        current: list[KeyResult],
        requested: list[UpdateKeyResultRequest],
    ) -> list[KeyResult]:
        current_by_id = {result.id: result for result in current}
        results: list[KeyResult] = []
        for request in requested:
            existing = current_by_id.get(request.id) if request.id else None
            if existing is None:
                if request.metric is None or request.target is None or request.due_date is None:
                    raise ValueError("new key result requires metric, target and due date")
                results.append(KeyResult(**request.model_dump(exclude={"id"}, exclude_none=True)))
                continue
            if request.metric is not None:
                existing.metric = request.metric
            if request.target is not None:
                existing.target = request.target
            if request.due_date is not None:
                existing.due_date = request.due_date
            if request.current_value is not None:
                existing.current_value = request.current_value
            if request.unit is not None:
                existing.unit = request.unit
            existing.updated_at = datetime.now(timezone.utc)
            results.append(existing)
        return results