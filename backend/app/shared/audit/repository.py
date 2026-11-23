from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.collection import AsyncCollection

from .models import AuditEvent


class AuditRepository(Protocol):
    async def ensure_indexes(self) -> None:
        ...

    async def append(self, event: AuditEvent) -> None:
        ...

    async def list_page(
        self,
        *,
        tenant_id: str,
        workspace_id: str,
        limit: int,
        cursor: "AuditEventCursor | None" = None,
        resource: str | None = None,
        resource_id: str | None = None,
        initiative_id: str | None = None,
    ) -> list[AuditEvent]:
        ...


@dataclass(frozen=True, slots=True)
class AuditEventCursor:
    created_at: datetime
    event_id: str


class MongoAuditRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [
                ("tenant_id", ASCENDING),
                ("workspace_id", ASCENDING),
                ("created_at", DESCENDING),
                ("event_id", DESCENDING),
            ],
            name="ix_audit_events_tenant_workspace_created_at",
        )
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("resource", ASCENDING), ("resource_id", ASCENDING)],
            name="ix_audit_events_resource",
        )
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("metadata.initiative_id", ASCENDING)],
            name="ix_audit_events_initiative",
        )
        await self._collection.create_index(
            [("correlation_id", ASCENDING)],
            name="ix_audit_events_correlation_id",
        )

    async def append(self, event: AuditEvent) -> None:
        await self._collection.insert_one(
            {
                "event_id": event.event_id,
                "tenant_id": event.tenant_id,
                "workspace_id": event.workspace_id,
                "actor": event.actor,
                "action": event.action,
                "resource": event.resource,
                "resource_id": event.resource_id,
                "before_version": event.before_version,
                "after_version": event.after_version,
                "assessment": event.assessment,
                "provider": event.provider,
                "model": event.model,
                "prompt": event.prompt,
                "correlation_id": event.correlation_id,
                "trace_id": event.trace_id,
                "metadata": event.metadata,
                "created_at": event.created_at,
            }
        )

    async def list_page(
        self,
        *,
        tenant_id: str,
        workspace_id: str,
        limit: int,
        cursor: AuditEventCursor | None = None,
        resource: str | None = None,
        resource_id: str | None = None,
        initiative_id: str | None = None,
    ) -> list[AuditEvent]:
        filters: dict[str, object] = {
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
        }
        if resource is not None:
            filters["resource"] = resource
        if resource_id is not None:
            filters["resource_id"] = resource_id
        if initiative_id is not None:
            filters["$or"] = [
                {"resource": "initiative", "resource_id": initiative_id},
                {"metadata.initiative_id": initiative_id},
            ]
        if cursor is not None:
            cursor_filter = [
                {"created_at": {"$lt": cursor.created_at}},
                {"created_at": cursor.created_at, "event_id": {"$lt": cursor.event_id}},
            ]
            if "$or" in filters:
                filters["$and"] = [{"$or": filters.pop("$or")}, {"$or": cursor_filter}]
            else:
                filters["$or"] = cursor_filter
        query = self._collection.find(
            filters,
            sort=[("created_at", DESCENDING), ("event_id", DESCENDING)],
            limit=limit,
        )
        return [self._from_document(document) async for document in query]

    @staticmethod
    def _from_document(document: dict[str, object]) -> AuditEvent:
        return AuditEvent(
            tenant_id=document["tenant_id"],
            workspace_id=document["workspace_id"],
            actor=document["actor"],
            action=document["action"],
            resource=document["resource"],
            resource_id=document["resource_id"],
            before_version=document.get("before_version"),
            after_version=document.get("after_version"),
            assessment=document.get("assessment"),
            provider=document.get("provider"),
            model=document.get("model"),
            prompt=document.get("prompt"),
            correlation_id=document.get("correlation_id"),
            trace_id=document.get("trace_id"),
            metadata=dict(document.get("metadata", {})),
            event_id=document["event_id"],
            created_at=document["created_at"],
        )