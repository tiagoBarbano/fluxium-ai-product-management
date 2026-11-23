from types import SimpleNamespace
from typing import Any, Protocol

from pymongo import ASCENDING
from pymongo.asynchronous.collection import AsyncCollection

from .domain.entities import Evidence
from .domain.enums import EvidenceOrigin, EvidenceType


class EvidenceRepository(Protocol):
    async def ensure_indexes(self) -> None: ...

    async def insert(self, tenant_id: str, evidence: Evidence) -> None: ...

    async def find_by_id(self, tenant_id: str, evidence_id: str) -> Evidence | None: ...

    async def list_by_problem(self, tenant_id: str, workspace_id: str, problem_id: str) -> list[Evidence]: ...


class ProblemReferenceRepository(Protocol):
    async def find_by_id(self, tenant_id: str, problem_id: str) -> object | None: ...


class HypothesisReferenceRepository(Protocol):
    async def find_by_id(self, tenant_id: str, hypothesis_id: str) -> object | None: ...


class MongoProblemReferenceRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def find_by_id(self, tenant_id: str, problem_id: str) -> object | None:
        document = await self._collection.find_one({"tenant_id": tenant_id, "id": problem_id})
        return SimpleNamespace(**document) if document else None


class MongoHypothesisReferenceRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def find_by_id(self, tenant_id: str, hypothesis_id: str) -> object | None:
        document = await self._collection.find_one({"tenant_id": tenant_id, "id": hypothesis_id})
        return SimpleNamespace(**document) if document else None


class MongoEvidenceRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("opportunity_id", ASCENDING), ("created_at", ASCENDING)],
            name="ix_evidence_tenant_workspace_opportunity_created",
        )
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("problem_id", ASCENDING)],
            name="ix_evidence_tenant_workspace_problem",
        )

    async def insert(self, tenant_id: str, evidence: Evidence) -> None:
        await self._collection.insert_one(self._to_document(tenant_id, evidence))

    async def find_by_id(self, tenant_id: str, evidence_id: str) -> Evidence | None:
        document = await self._collection.find_one({"tenant_id": tenant_id, "id": evidence_id})
        return self._from_document(document) if document else None

    async def list_by_problem(self, tenant_id: str, workspace_id: str, problem_id: str) -> list[Evidence]:
        cursor = self._collection.find(
            {"tenant_id": tenant_id, "workspace_id": workspace_id, "problem_id": problem_id},
            sort=[("created_at", ASCENDING), ("id", ASCENDING)],
        )
        return [self._from_document(document) async for document in cursor]

    @staticmethod
    def _to_document(tenant_id: str, evidence: Evidence) -> dict[str, Any]:
        return {
            "id": evidence.id,
            "tenant_id": tenant_id,
            "workspace_id": evidence.workspace_id,
            "opportunity_id": evidence.opportunity_id,
            "problem_id": evidence.problem_id,
            "hypothesis_id": evidence.hypothesis_id,
            "type": evidence.type.value,
            "origin": evidence.origin.value,
            "description": evidence.description,
            "source": evidence.source,
            "reference": evidence.reference,
            "created_by": evidence.created_by,
            "created_at": evidence.created_at,
            "updated_at": evidence.updated_at,
        }

    @staticmethod
    def _from_document(document: dict[str, Any]) -> Evidence:
        return Evidence(
            id=document["id"],
            workspace_id=document["workspace_id"],
            opportunity_id=document["opportunity_id"],
            problem_id=document.get("problem_id"),
            hypothesis_id=document.get("hypothesis_id"),
            type=EvidenceType(document["type"]),
            origin=EvidenceOrigin(document["origin"]),
            description=document["description"],
            source=document.get("source"),
            reference=document.get("reference"),
            created_by=document["created_by"],
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )