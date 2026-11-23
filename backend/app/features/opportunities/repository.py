from datetime import UTC, datetime
from typing import Any, Protocol

from pymongo import ASCENDING, ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection

from .domain.entities import Opportunity
from .domain.enums import OpportunityStatus


class OpportunityRepository(Protocol):
    async def insert(self, tenant_id: str, opportunity: Opportunity) -> None:
        ...

    async def find_by_id(self, tenant_id: str, opportunity_id: str) -> Opportunity | None:
        ...

    async def list_by_workspace(self, tenant_id: str, workspace_id: str) -> list[Opportunity]:
        ...

    async def replace(self, tenant_id: str, opportunity: Opportunity, expected_version: int) -> bool:
        ...

    async def transition_new_to_discovery(self, tenant_id: str, opportunity_id: str, expected_version: int) -> Opportunity | None:
        ...


class MongoOpportunityRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("id", ASCENDING)],
            name="ix_opportunities_tenant_workspace_id",
        )

    async def insert(self, tenant_id: str, opportunity: Opportunity) -> None:
        await self._collection.insert_one(self._to_document(tenant_id, opportunity))

    async def find_by_id(self, tenant_id: str, opportunity_id: str) -> Opportunity | None:
        document = await self._collection.find_one({"tenant_id": tenant_id, "id": opportunity_id})
        return self._from_document(document) if document else None

    async def list_by_workspace(self, tenant_id: str, workspace_id: str) -> list[Opportunity]:
        cursor = self._collection.find(
            {"tenant_id": tenant_id, "workspace_id": workspace_id},
            sort=[("id", ASCENDING)],
        )
        return [self._from_document(document) async for document in cursor]

    async def replace(self, tenant_id: str, opportunity: Opportunity, expected_version: int) -> bool:
        result = await self._collection.replace_one(
            {"tenant_id": tenant_id, "id": opportunity.id, "version": expected_version},
            self._to_document(tenant_id, opportunity),
        )
        return result.modified_count == 1

    async def transition_new_to_discovery(self, tenant_id: str, opportunity_id: str, expected_version: int) -> Opportunity | None:
        result = await self._collection.find_one_and_update(
            {"tenant_id": tenant_id, "id": opportunity_id, "status": OpportunityStatus.NEW.value, "version": expected_version},
            {"$set": {"status": OpportunityStatus.DISCOVERY.value, "updated_at": datetime.now(UTC)}, "$inc": {"version": 1}},
            return_document=ReturnDocument.AFTER,
        )
        return self._from_document(result) if result else None

    @staticmethod
    def _to_document(tenant_id: str, opportunity: Opportunity) -> dict[str, Any]:
        return {
            "id": opportunity.id,
            "tenant_id": tenant_id,
            "workspace_id": opportunity.workspace_id,
            "product_id": opportunity.product_id,
            "title": opportunity.title,
            "description": opportunity.description,
            "objective_ids": opportunity.objective_ids,
            "status": opportunity.status.value,
            "created_by": opportunity.created_by,
            "created_at": opportunity.created_at,
            "updated_at": opportunity.updated_at,
            "version": opportunity.version,
        }

    @staticmethod
    def _from_document(document: dict[str, Any]) -> Opportunity:
        return Opportunity(
            id=document["id"],
            product_id=document["product_id"],
            title=document["title"],
            description=document["description"],
            objective_ids=document.get("objective_ids", []),
            status=OpportunityStatus(document["status"]),
            workspace_id=document.get("workspace_id"),
            created_by=document.get("created_by"),
            created_at=document.get("created_at", datetime.now(UTC)),
            updated_at=document.get("updated_at", datetime.now(UTC)),
            version=document.get("version", 1),
        )