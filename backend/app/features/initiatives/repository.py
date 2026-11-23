from typing import Any, Protocol

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.collection import AsyncCollection

from .domain.entities import Initiative
from .domain.enums import InitiativeStatus


class InitiativeRepository(Protocol):
    async def ensure_indexes(self) -> None: ...
    async def insert(self, tenant_id: str, initiative: Initiative) -> None: ...
    async def find_by_id(self, tenant_id: str, initiative_id: str) -> Initiative | None: ...
    async def list_by_product(self, tenant_id: str, workspace_id: str, product_id: str) -> list[Initiative]: ...
    async def list_by_opportunity(self, tenant_id: str, workspace_id: str, opportunity_id: str) -> list[Initiative]: ...
    async def list_by_workspace(self, tenant_id: str, workspace_id: str) -> list[Initiative]: ...
    async def replace(self, tenant_id: str, initiative: Initiative, expected_version: int) -> bool: ...


class MongoInitiativeRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("product_id", ASCENDING), ("status", ASCENDING), ("updated_at", DESCENDING)],
            name="ix_initiatives_tenant_workspace_product_status_updated",
        )
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("id", ASCENDING)],
            name="ix_initiatives_tenant_workspace_id",
            unique=True,
        )

    async def insert(self, tenant_id: str, initiative: Initiative) -> None:
        await self._collection.insert_one(self._to_document(tenant_id, initiative))

    async def find_by_id(self, tenant_id: str, initiative_id: str) -> Initiative | None:
        document = await self._collection.find_one({"tenant_id": tenant_id, "id": initiative_id})
        return self._from_document(document) if document else None

    async def list_by_product(self, tenant_id: str, workspace_id: str, product_id: str) -> list[Initiative]:
        cursor = self._collection.find(
            {"tenant_id": tenant_id, "workspace_id": workspace_id, "product_id": product_id},
            sort=[("updated_at", DESCENDING), ("id", ASCENDING)],
        )
        return [self._from_document(document) async for document in cursor]

    async def list_by_opportunity(self, tenant_id: str, workspace_id: str, opportunity_id: str) -> list[Initiative]:
        cursor = self._collection.find(
            {"tenant_id": tenant_id, "workspace_id": workspace_id, "opportunity_id": opportunity_id},
            sort=[("updated_at", DESCENDING), ("id", ASCENDING)],
        )
        return [self._from_document(document) async for document in cursor]

    async def list_by_workspace(self, tenant_id: str, workspace_id: str) -> list[Initiative]:
        cursor = self._collection.find(
            {"tenant_id": tenant_id, "workspace_id": workspace_id},
            sort=[("updated_at", DESCENDING), ("id", ASCENDING)],
        )
        return [self._from_document(document) async for document in cursor]

    async def replace(self, tenant_id: str, initiative: Initiative, expected_version: int) -> bool:
        result = await self._collection.replace_one(
            {"tenant_id": tenant_id, "workspace_id": initiative.workspace_id, "id": initiative.id, "version": expected_version},
            self._to_document(tenant_id, initiative),
        )
        return result.modified_count == 1

    @staticmethod
    def _to_document(tenant_id: str, initiative: Initiative) -> dict[str, Any]:
        return {
            "id": initiative.id,
            "tenant_id": tenant_id,
            "workspace_id": initiative.workspace_id,
            "product_id": initiative.product_id,
            "opportunity_id": initiative.opportunity_id,
            "problem_id": initiative.problem_id,
            "title": initiative.title,
            "objective": initiative.objective,
            "hypothesis_ids": initiative.hypothesis_ids,
            "objective_ids": initiative.objective_ids,
            "evidence_ids": initiative.evidence_ids,
            "scope": initiative.scope,
            "out_of_scope": initiative.out_of_scope,
            "status": initiative.status.value,
            "readiness_score": initiative.readiness_score,
            "readiness_confidence": initiative.readiness_confidence,
            "delivery_confidence": initiative.delivery_confidence,
            "outcome_confidence": initiative.outcome_confidence,
            "created_by": initiative.created_by,
            "created_at": initiative.created_at,
            "updated_at": initiative.updated_at,
            "version": initiative.version,
        }

    @staticmethod
    def _from_document(document: dict[str, Any]) -> Initiative:
        return Initiative(
            id=document["id"], workspace_id=document["workspace_id"], product_id=document["product_id"],
            opportunity_id=document["opportunity_id"], problem_id=document.get("problem_id"), title=document["title"],
            objective=document["objective"], hypothesis_ids=document.get("hypothesis_ids", []),
            objective_ids=document.get("objective_ids", []), evidence_ids=document.get("evidence_ids", []),
            scope=document["scope"], out_of_scope=document.get("out_of_scope"),
            status=InitiativeStatus(document["status"]), readiness_score=document.get("readiness_score"),
            readiness_confidence=document.get("readiness_confidence"), delivery_confidence=document.get("delivery_confidence"),
            outcome_confidence=document.get("outcome_confidence"), created_by=document["created_by"],
            created_at=document["created_at"], updated_at=document["updated_at"], version=document["version"],
        )