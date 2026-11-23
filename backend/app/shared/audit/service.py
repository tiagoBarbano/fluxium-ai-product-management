import base64
import binascii
import json
from datetime import datetime
from typing import Any

from .models import AuditEvent
from .repository import AuditEventCursor, AuditRepository
from .schemas import AuditEventPage, AuditEventQuery, AuditEventResponse


class AuditService:
    def __init__(self, repository: AuditRepository) -> None:
        self._repository = repository

    async def record(
        self,
        *,
        tenant_id: str,
        workspace_id: str,
        actor: str,
        action: str,
        resource: str,
        resource_id: str,
        before_version: int | None = None,
        after_version: int | None = None,
        assessment: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        prompt: str | None = None,
        correlation_id: str | None = None,
        trace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            actor=actor,
            action=action,
            resource=resource,
            resource_id=resource_id,
            before_version=before_version,
            after_version=after_version,
            assessment=assessment,
            provider=provider,
            model=model,
            prompt=prompt,
            correlation_id=correlation_id,
            trace_id=trace_id,
            metadata={} if metadata is None else dict(metadata),
        )
        await self._repository.append(event)
        return event

    async def list_page(
        self,
        *,
        tenant_id: str,
        workspace_id: str,
        query: AuditEventQuery | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        resource: str | None = None,
        resource_id: str | None = None,
        initiative_id: str | None = None,
    ) -> AuditEventPage:
        request = query or AuditEventQuery(
            limit=20 if limit is None else limit,
            cursor=cursor,
            resource=resource,
            resource_id=resource_id,
            initiative_id=initiative_id,
        )
        decoded_cursor = self._decode_cursor(request.cursor)
        events = await self._repository.list_page(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            limit=request.limit + 1,
            cursor=decoded_cursor,
            resource=request.resource,
            resource_id=request.resource_id,
            initiative_id=request.initiative_id,
        )
        has_next_page = len(events) > request.limit
        page_events = events[: request.limit]
        next_cursor = self._encode_cursor(page_events[-1]) if has_next_page else None
        return AuditEventPage(
            items=[AuditEventResponse.from_event(event) for event in page_events],
            next_cursor=next_cursor,
        )

    @staticmethod
    def _encode_cursor(event: AuditEvent) -> str:
        payload = json.dumps(
            {"created_at": event.created_at.isoformat(), "event_id": event.event_id},
            separators=(",", ":"),
        ).encode()
        return base64.urlsafe_b64encode(payload).decode().rstrip("=")

    @staticmethod
    def _decode_cursor(value: str | None) -> AuditEventCursor | None:
        if value is None:
            return None
        try:
            padded = value + "=" * (-len(value) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded).decode())
            return AuditEventCursor(
                created_at=datetime.fromisoformat(payload["created_at"]),
                event_id=payload["event_id"],
            )
        except (binascii.Error, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid audit event cursor") from exc