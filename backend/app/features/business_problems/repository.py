from typing import Any, Protocol

from pymongo import ASCENDING
from pymongo.asynchronous.collection import AsyncCollection

from .domain.entities import BusinessProblem
from .domain.enums import BusinessProblemStatus


class BusinessProblemRepository(Protocol):
    async def ensure_indexes(self) -> None: ...

    async def insert(self, tenant_id: str, problem: BusinessProblem) -> None: ...

    async def find_by_id(
        self,
        tenant_id: str,
        workspace_ids: set[str],
        problem_id: str,
    ) -> BusinessProblem | None: ...

    async def replace(
        self,
        tenant_id: str,
        problem: BusinessProblem,
        expected_version: int,
    ) -> bool: ...


class MongoBusinessProblemRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("id", ASCENDING)],
            name="ix_business_problems_tenant_workspace_id",
            unique=True,
        )
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("opportunity_id", ASCENDING)],
            name="ix_business_problems_tenant_workspace_opportunity",
        )

    async def insert(self, tenant_id: str, problem: BusinessProblem) -> None:
        await self._collection.insert_one(self._to_document(tenant_id, problem))

    async def find_by_id(
        self,
        tenant_id: str,
        workspace_ids: set[str],
        problem_id: str,
    ) -> BusinessProblem | None:
        document = await self._collection.find_one(
            {"tenant_id": tenant_id, "workspace_id": {"$in": list(workspace_ids)}, "id": problem_id}
        )
        return self._from_document(document) if document else None

    async def replace(self, tenant_id: str, problem: BusinessProblem, expected_version: int) -> bool:
        result = await self._collection.replace_one(
            {
                "tenant_id": tenant_id,
                "workspace_id": problem.workspace_id,
                "id": problem.id,
                "version": expected_version,
            },
            self._to_document(tenant_id, problem),
        )
        return result.modified_count == 1

    @staticmethod
    def _to_document(tenant_id: str, problem: BusinessProblem) -> dict[str, Any]:
        return {
            "id": problem.id,
            "tenant_id": tenant_id,
            "workspace_id": problem.workspace_id,
            "product_id": problem.product_id,
            "opportunity_id": problem.opportunity_id,
            "description": problem.description,
            "audience": problem.audience,
            "reported_impact": problem.reported_impact,
            "estimated_impact": problem.estimated_impact,
            "status": problem.status.value,
            "created_by": problem.created_by,
            "created_at": problem.created_at,
            "updated_at": problem.updated_at,
            "version": problem.version,
        }

    @staticmethod
    def _from_document(document: dict[str, Any]) -> BusinessProblem:
        return BusinessProblem(
            id=document["id"],
            workspace_id=document["workspace_id"],
            product_id=document["product_id"],
            opportunity_id=document["opportunity_id"],
            description=document["description"],
            audience=document["audience"],
            reported_impact=document["reported_impact"],
            estimated_impact=document.get("estimated_impact"),
            status=BusinessProblemStatus(document["status"]),
            created_by=document["created_by"],
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            version=document["version"],
        )