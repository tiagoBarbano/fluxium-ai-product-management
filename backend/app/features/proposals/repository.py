from datetime import UTC, datetime
from collections.abc import Collection
from typing import Any, Protocol

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.collection import AsyncCollection

from .domain.entities import Proposal
from .domain.enums import ProposalStatus


class ProposalRepository(Protocol):
    async def ensure_indexes(self) -> None: ...
    async def insert(self, tenant_id: str, proposal: Proposal) -> None: ...
    async def find_by_id(self, tenant_id: str, proposal_id: str) -> Proposal | None: ...
    async def list_by_assessment(self, tenant_id: str, initiative_id: str, assessment_id: str) -> list[Proposal]: ...
    async def list_by_initiative(self, tenant_id: str, initiative_id: str, status: ProposalStatus | None, limit: int) -> list[Proposal]: ...
    async def list_by_status(self, tenant_id: str, status: ProposalStatus, limit: int) -> list[Proposal]: ...
    async def list_by_initiatives(self, tenant_id: str, initiative_ids: Collection[str], status: ProposalStatus | None, limit: int) -> list[Proposal]: ...
    async def decide(self, tenant_id: str, proposal: Proposal, status: ProposalStatus, decided_by: str, reason: str | None) -> bool: ...


class MongoProposalRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("initiative_id", ASCENDING), ("assessment_id", ASCENDING), ("created_at", DESCENDING)],
            name="ix_proposals_tenant_initiative_assessment_created",
        )
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("initiative_id", ASCENDING), ("created_at", DESCENDING), ("id", ASCENDING)],
            name="ix_proposals_tenant_initiative_created",
        )
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("initiative_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
            name="ix_proposals_tenant_initiative_status_created",
        )
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("id", ASCENDING)],
            name="ix_proposals_tenant_id",
            unique=True,
        )

    async def insert(self, tenant_id: str, proposal: Proposal) -> None:
        await self._collection.insert_one(self._to_document(tenant_id, proposal))

    async def find_by_id(self, tenant_id: str, proposal_id: str) -> Proposal | None:
        document = await self._collection.find_one({"tenant_id": tenant_id, "id": proposal_id})
        return self._from_document(document) if document else None

    async def list_by_assessment(self, tenant_id: str, initiative_id: str, assessment_id: str) -> list[Proposal]:
        cursor = self._collection.find(
            {"tenant_id": tenant_id, "initiative_id": initiative_id, "assessment_id": assessment_id},
            sort=[("created_at", DESCENDING), ("id", ASCENDING)],
        )
        return [self._from_document(document) async for document in cursor]

    async def list_by_initiative(self, tenant_id: str, initiative_id: str, status: ProposalStatus | None, limit: int) -> list[Proposal]:
        filters: dict[str, Any] = {"tenant_id": tenant_id, "initiative_id": initiative_id}
        if status is not None:
            filters["status"] = status.value
        cursor = self._collection.find(
            filters,
            sort=[("created_at", DESCENDING), ("id", ASCENDING)],
            limit=limit,
        )
        return [self._from_document(document) async for document in cursor]

    async def list_by_status(self, tenant_id: str, status: ProposalStatus, limit: int) -> list[Proposal]:
        cursor = self._collection.find(
            {"tenant_id": tenant_id, "status": status.value},
            sort=[("created_at", DESCENDING), ("id", ASCENDING)],
            limit=limit,
        )
        return [self._from_document(document) async for document in cursor]

    async def list_by_initiatives(
        self, tenant_id: str, initiative_ids: Collection[str], status: ProposalStatus | None, limit: int
    ) -> list[Proposal]:
        filters: dict[str, Any] = {"tenant_id": tenant_id, "initiative_id": {"$in": list(initiative_ids)}}
        if status is not None:
            filters["status"] = status.value
        cursor = self._collection.find(filters, sort=[("created_at", DESCENDING), ("id", ASCENDING)], limit=limit)
        return [self._from_document(document) async for document in cursor]

    async def decide(self, tenant_id: str, proposal: Proposal, status: ProposalStatus, decided_by: str, reason: str | None) -> bool:
        result = await self._collection.update_one(
            {"tenant_id": tenant_id, "id": proposal.id, "status": ProposalStatus.PENDING.value},
            {
                "$set": {
                    "status": status.value,
                    "decided_by": decided_by,
                    "decision_reason": reason,
                    "decided_at": datetime.now(UTC),
                }
            },
        )
        return result.modified_count == 1

    @staticmethod
    def _to_document(tenant_id: str, proposal: Proposal) -> dict[str, Any]:
        return {
            "id": proposal.id,
            "tenant_id": tenant_id,
            "initiative_id": proposal.initiative_id,
            "assessment_id": proposal.assessment_id,
            "changes": proposal.changes,
            "status": proposal.status.value,
            "created_by": proposal.created_by,
            "decided_by": proposal.decided_by,
            "decision_reason": proposal.decision_reason,
            "created_at": proposal.created_at,
            "decided_at": proposal.decided_at,
            "expected_initiative_version": proposal.expected_initiative_version,
            "business_document": proposal.business_document,
        }

    @staticmethod
    def _from_document(document: dict[str, Any]) -> Proposal:
        return Proposal(
            id=document["id"],
            initiative_id=document["initiative_id"],
            assessment_id=document["assessment_id"],
            changes=document["changes"],
            status=ProposalStatus(document["status"]),
            created_by=document["created_by"],
            decided_by=document.get("decided_by"),
            decision_reason=document.get("decision_reason"),
            created_at=document["created_at"],
            decided_at=document.get("decided_at"),
            expected_initiative_version=document["expected_initiative_version"],
            business_document=document.get("business_document", {}),
        )