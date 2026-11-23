from typing import Any, Protocol

from pymongo import ASCENDING
from pymongo.asynchronous.collection import AsyncCollection

from .domain.entities import Hypothesis
from .domain.enums import HypothesisStatus


class HypothesisRepository(Protocol):
    async def ensure_indexes(self) -> None: ...
    async def insert(self, tenant_id: str, hypothesis: Hypothesis) -> None: ...
    async def find_by_id(self, tenant_id: str, hypothesis_id: str) -> Hypothesis | None: ...
    async def list_by_opportunity(self, tenant_id: str, workspace_id: str, opportunity_id: str) -> list[Hypothesis]: ...
    async def replace(self, tenant_id: str, hypothesis: Hypothesis, expected_version: int) -> bool: ...


class MongoHypothesisRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("opportunity_id", ASCENDING), ("created_at", ASCENDING)],
            name="ix_hypotheses_tenant_workspace_opportunity_created",
        )

    async def insert(self, tenant_id: str, hypothesis: Hypothesis) -> None:
        await self._collection.insert_one(self._to_document(tenant_id, hypothesis))

    async def find_by_id(self, tenant_id: str, hypothesis_id: str) -> Hypothesis | None:
        document = await self._collection.find_one({"tenant_id": tenant_id, "id": hypothesis_id})
        return self._from_document(document) if document else None

    async def list_by_opportunity(self, tenant_id: str, workspace_id: str, opportunity_id: str) -> list[Hypothesis]:
        cursor = self._collection.find(
            {"tenant_id": tenant_id, "workspace_id": workspace_id, "opportunity_id": opportunity_id},
            sort=[("created_at", ASCENDING), ("id", ASCENDING)],
        )
        return [self._from_document(document) async for document in cursor]

    async def replace(self, tenant_id: str, hypothesis: Hypothesis, expected_version: int) -> bool:
        result = await self._collection.replace_one(
            {"tenant_id": tenant_id, "workspace_id": hypothesis.workspace_id, "id": hypothesis.id, "version": expected_version},
            self._to_document(tenant_id, hypothesis),
        )
        return result.modified_count == 1

    @staticmethod
    def _to_document(tenant_id: str, hypothesis: Hypothesis) -> dict[str, Any]:
        return {
            "id": hypothesis.id,
            "tenant_id": tenant_id,
            "workspace_id": hypothesis.workspace_id,
            "opportunity_id": hypothesis.opportunity_id,
            "statement": hypothesis.statement,
            "expected_behavior": hypothesis.expected_behavior,
            "expected_outcome": hypothesis.expected_outcome,
            "evidence_ids": hypothesis.evidence_ids,
            "confidence": hypothesis.confidence,
            "status": hypothesis.status.value,
            "created_by": hypothesis.created_by,
            "created_at": hypothesis.created_at,
            "updated_at": hypothesis.updated_at,
            "version": hypothesis.version,
        }

    @staticmethod
    def _from_document(document: dict[str, Any]) -> Hypothesis:
        return Hypothesis(
            id=document["id"], workspace_id=document["workspace_id"], opportunity_id=document["opportunity_id"],
            statement=document["statement"], expected_behavior=document["expected_behavior"], expected_outcome=document["expected_outcome"],
            evidence_ids=document.get("evidence_ids", []), confidence=document["confidence"], status=HypothesisStatus(document["status"]),
            created_by=document["created_by"], created_at=document["created_at"], updated_at=document["updated_at"], version=document["version"],
        )