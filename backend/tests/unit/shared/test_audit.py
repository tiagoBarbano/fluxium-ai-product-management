from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.shared.audit import AuditEventQuery, AuditService
from app.shared.audit.models import AuditEvent
from app.shared.audit.repository import AuditEventCursor, MongoAuditRepository


class FakeAuditRepository:
    def __init__(self) -> None:
        self.events = []

    async def append(self, event) -> None:
        self.events.append(event)


class FakeCollection:
    def __init__(self) -> None:
        self.indexes = []
        self.documents = []
        self.find_calls = []

    async def create_index(self, keys, **options):
        self.indexes.append((keys, options))

    async def insert_one(self, document) -> None:
        self.documents.append(document)

    def find(self, filters, *, sort, limit):
        self.find_calls.append((filters, sort, limit))
        return FakeCursor(self.documents[:limit])


class FakeCursor:
    def __init__(self, documents) -> None:
        self.documents = documents

    def __aiter__(self):
        return self._iterate()

    async def _iterate(self):
        for document in self.documents:
            yield document


class FakePagedAuditRepository:
    def __init__(self, events) -> None:
        self.events = events
        self.calls = []

    async def list_page(self, **kwargs):
        self.calls.append(kwargs)
        return self.events


def make_event(event_id: str, created_at: datetime) -> AuditEvent:
    return AuditEvent(
        tenant_id="tenant-1",
        workspace_id="workspace-1",
        actor="user-1",
        action="UPDATED",
        resource="product",
        resource_id=event_id,
        event_id=event_id,
        created_at=created_at,
    )


@pytest.mark.asyncio
async def test_audit_service_records_scoped_event_and_ai_context() -> None:
    repository = FakeAuditRepository()
    event = await AuditService(repository).record(
        tenant_id="tenant-1",
        workspace_id="workspace-1",
        actor="user-1",
        action="ASSESSMENT_COMPLETED",
        resource="assessment",
        resource_id="assessment-1",
        before_version=1,
        after_version=2,
        assessment="readiness",
        provider="openai",
        model="gpt-5",
        prompt="Assess this product",
        correlation_id="corr-1",
        trace_id="trace-1",
    )

    assert repository.events == [event]
    assert event.tenant_id == "tenant-1"
    assert event.workspace_id == "workspace-1"
    assert event.model == "gpt-5"
    with pytest.raises(FrozenInstanceError):
        event.action = "CHANGED"


@pytest.mark.asyncio
async def test_mongo_repository_creates_scoped_indexes_and_document() -> None:
    collection = FakeCollection()
    repository = MongoAuditRepository(collection)
    event = AuditEvent(
        tenant_id="tenant-1",
        workspace_id="workspace-1",
        actor="user-1",
        action="UPDATED",
        resource="product",
        resource_id="product-1",
    )

    await repository.ensure_indexes()
    await repository.append(event)

    names = {options["name"] for _, options in collection.indexes}
    assert names == {
        "ix_audit_events_tenant_workspace_created_at",
        "ix_audit_events_resource",
        "ix_audit_events_initiative",
        "ix_audit_events_correlation_id",
    }
    assert collection.documents[0]["tenant_id"] == "tenant-1"
    assert collection.documents[0]["workspace_id"] == "workspace-1"


@pytest.mark.asyncio
async def test_mongo_repository_scopes_page_to_tenant_and_workspace() -> None:
    collection = FakeCollection()
    repository = MongoAuditRepository(collection)
    cursor = AuditEventCursor(
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        event_id="event-2",
    )

    await repository.list_page(
        tenant_id="tenant-2",
        workspace_id="workspace-2",
        limit=10,
        cursor=cursor,
    )

    filters, sort, limit = collection.find_calls[0]
    assert filters == {
        "tenant_id": "tenant-2",
        "workspace_id": "workspace-2",
        "$or": [
            {"created_at": {"$lt": cursor.created_at}},
            {"created_at": cursor.created_at, "event_id": {"$lt": "event-2"}},
        ],
    }
    assert sort == [("created_at", -1), ("event_id", -1)]
    assert limit == 10


@pytest.mark.asyncio
async def test_mongo_repository_applies_resource_and_initiative_filters_with_cursor() -> None:
    collection = FakeCollection()
    repository = MongoAuditRepository(collection)
    cursor = AuditEventCursor(
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        event_id="event-2",
    )

    await repository.list_page(
        tenant_id="tenant-1",
        workspace_id="workspace-1",
        limit=10,
        cursor=cursor,
        resource="proposal",
        resource_id="proposal-1",
        initiative_id="initiative-1",
    )

    filters, _, _ = collection.find_calls[0]
    assert filters["resource"] == "proposal"
    assert filters["resource_id"] == "proposal-1"
    assert filters["$and"][0]["$or"] == [
        {"resource": "initiative", "resource_id": "initiative-1"},
        {"metadata.initiative_id": "initiative-1"},
    ]
    assert filters["$and"][1]["$or"] == [
        {"created_at": {"$lt": cursor.created_at}},
        {"created_at": cursor.created_at, "event_id": {"$lt": "event-2"}},
    ]


@pytest.mark.asyncio
async def test_audit_service_enforces_maximum_limit_and_fetches_next_item() -> None:
    events = [
        make_event(f"event-{index}", datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index))
        for index in range(3)
    ]
    repository = FakePagedAuditRepository(events)
    service = AuditService(repository)

    page = await service.list_page(
        tenant_id="tenant-1",
        workspace_id="workspace-1",
        limit=2,
    )

    assert len(page.items) == 2
    assert page.next_cursor is not None
    assert repository.calls[0]["limit"] == 3

    with pytest.raises(ValidationError):
        await service.list_page(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            limit=101,
        )


@pytest.mark.asyncio
async def test_audit_service_passes_stable_cursor_to_repository() -> None:
    events = [
        make_event("event-1", datetime(2026, 1, 1, tzinfo=UTC)),
        make_event("event-2", datetime(2026, 1, 2, tzinfo=UTC)),
    ]
    repository = FakePagedAuditRepository(events)
    service = AuditService(repository)

    first_page = await service.list_page(
        tenant_id="tenant-1",
        workspace_id="workspace-1",
        limit=1,
    )
    await service.list_page(
        tenant_id="tenant-1",
        workspace_id="workspace-1",
        query=AuditEventQuery(limit=1, cursor=first_page.next_cursor),
    )

    cursor = repository.calls[1]["cursor"]
    assert cursor == AuditEventCursor(created_at=events[0].created_at, event_id="event-1")


@pytest.mark.asyncio
async def test_audit_service_returns_empty_page_without_cursor() -> None:
    repository = FakePagedAuditRepository([])

    page = await AuditService(repository).list_page(
        tenant_id="tenant-1",
        workspace_id="workspace-1",
    )

    assert page.items == []
    assert page.next_cursor is None