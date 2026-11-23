from copy import deepcopy

import pytest
from pymongo.errors import DuplicateKeyError

from app.features.discovery.schemas.requests import CreateDiscoveryMessageRequest, UpdateDiscoveryContextRequest
from app.features.discovery.service import DiscoveryConflictError, DiscoveryService
from app.features.opportunities.domain.entities import Opportunity
from app.features.opportunities.domain.enums import OpportunityStatus


class FakeOpportunityRepository:
    def __init__(self, opportunity: Opportunity | None) -> None:
        self.opportunity = opportunity

    async def find_by_id(self, tenant_id: str, opportunity_id: str) -> Opportunity | None:
        return self.opportunity if self.opportunity and self.opportunity.id == opportunity_id else None

    async def replace(self, tenant_id: str, opportunity: Opportunity, expected_version: int = 1) -> bool:
        self.opportunity = opportunity
        return True


class FakeDiscoveryRepository:
    def __init__(self) -> None:
        self.sessions = {}
        self.messages = []

    async def ensure_indexes(self) -> None: pass
    async def insert_session(self, tenant_id: str, session) -> None: self.sessions[session.id] = deepcopy(session)
    async def find_session(self, tenant_id: str, session_id: str): return deepcopy(self.sessions.get(session_id))
    async def find_active_for_opportunity(self, tenant_id: str, opportunity_id: str):
        return next((session for session in self.sessions.values() if session.opportunity_id == opportunity_id and session.status.value in {"ACTIVE", "PAUSED"}), None)
    async def replace_session(self, tenant_id: str, session, expected_version: int) -> bool:
        current = self.sessions.get(session.id)
        if current is None or current.version != expected_version:
            return False
        self.sessions[session.id] = deepcopy(session)
        return True
    async def insert_message(self, tenant_id: str, workspace_id: str, message) -> None: self.messages.append(message)
    async def list_messages(self, tenant_id: str, session_id: str): return sorted((message for message in self.messages if message.session_id == session_id), key=lambda message: message.sequence)
    async def next_sequence(self, tenant_id: str, session_id: str) -> int: return len([message for message in self.messages if message.session_id == session_id]) + 1


class RetryingDiscoveryRepository(FakeDiscoveryRepository):
    def __init__(self) -> None:
        super().__init__()
        self.fail_next_insert = True

    async def insert_message(self, tenant_id: str, workspace_id: str, message) -> None:
        if self.fail_next_insert:
            self.fail_next_insert = False
            self.messages.append(message)
            raise DuplicateKeyError("simulated sequence race")
        await super().insert_message(tenant_id, workspace_id, message)


@pytest.fixture
def service() -> tuple[DiscoveryService, FakeOpportunityRepository, FakeDiscoveryRepository]:
    opportunity_repository = FakeOpportunityRepository(Opportunity("opp-1", "product-1", "Improve onboarding", "Reduce friction.", workspace_id="ws-1"))
    discovery_repository = FakeDiscoveryRepository()
    return DiscoveryService(discovery_repository, opportunity_repository), opportunity_repository, discovery_repository


@pytest.mark.asyncio
async def test_start_moves_opportunity_to_discovery_and_is_workspace_scoped(service) -> None:
    discovery_service, opportunity_repository, _ = service

    session = await discovery_service.start("opp-1", "tenant-1", "user-1", {"ws-1"})

    assert session.workspace_id == "ws-1"
    assert opportunity_repository.opportunity.status is OpportunityStatus.DISCOVERY


@pytest.mark.asyncio
async def test_active_session_cannot_be_started_twice(service) -> None:
    discovery_service, _, _ = service
    await discovery_service.start("opp-1", "tenant-1", "user-1", {"ws-1"})

    with pytest.raises(DiscoveryConflictError, match="already exists"):
        await discovery_service.start("opp-1", "tenant-1", "user-1", {"ws-1"})


@pytest.mark.asyncio
async def test_messages_are_sequenced_and_context_uses_optimistic_version(service) -> None:
    discovery_service, _, _ = service
    session = await discovery_service.start("opp-1", "tenant-1", "user-1", {"ws-1"})

    first = await discovery_service.add_message(session.id, CreateDiscoveryMessageRequest(content="What is the problem?"), "tenant-1", "user-1", {"ws-1"})
    second = await discovery_service.add_message(session.id, CreateDiscoveryMessageRequest(content="Onboarding is unclear."), "tenant-1", "user-1", {"ws-1"})
    updated = await discovery_service.update_context(session.id, UpdateDiscoveryContextRequest(observed_problem="Onboarding is unclear.", expected_version=1), "tenant-1", {"ws-1"})

    assert (first.sequence, second.sequence) == (1, 2)
    assert updated.version == 2


@pytest.mark.asyncio
async def test_message_sequence_retries_after_duplicate_key(service) -> None:
    _, opportunity_repository, _ = service
    repository = RetryingDiscoveryRepository()
    discovery_service = DiscoveryService(repository, opportunity_repository)
    session = await discovery_service.start("opp-1", "tenant-1", "user-1", {"ws-1"})

    message = await discovery_service.add_message(
        session.id,
        CreateDiscoveryMessageRequest(content="Retry safely."),
        "tenant-1",
        "user-1",
        {"ws-1"},
    )

    assert message.sequence == 2