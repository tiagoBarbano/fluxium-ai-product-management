from datetime import UTC, datetime

from pymongo.errors import DuplicateKeyError

from ..opportunities.domain.enums import OpportunityStatus
from ..opportunities.repository import OpportunityRepository
from .domain.entities import DiscoveryContext, DiscoveryMessage, DiscoverySession
from .domain.enums import DiscoverySessionStatus
from .repository import DiscoveryRepository
from .schemas.requests import CreateDiscoveryMessageRequest, DiscoveryContextRequest, UpdateDiscoveryContextRequest


class DiscoveryNotFoundError(LookupError): pass
class DiscoveryAccessError(PermissionError): pass
class DiscoveryConflictError(ValueError): pass


class DiscoveryService:
    def __init__(self, repository: DiscoveryRepository, opportunities: OpportunityRepository) -> None:
        self._repository = repository
        self._opportunities = opportunities

    async def start(self, opportunity_id: str, tenant_id: str, subject: str, workspace_ids: set[str]) -> DiscoverySession:
        opportunity = await self._opportunities.find_by_id(tenant_id, opportunity_id)
        self._check_opportunity(opportunity, workspace_ids)
        existing = await self._repository.find_active_for_opportunity(tenant_id, opportunity_id)
        if existing is not None:
            raise DiscoveryConflictError("An active discovery session already exists")
        if opportunity.status is not OpportunityStatus.NEW:
            raise DiscoveryConflictError("Opportunity cannot start a new discovery session")
        transition = getattr(self._opportunities, "transition_new_to_discovery", None)
        if transition is not None:
            transitioned = await transition(tenant_id, opportunity.id, opportunity.version)
            if transitioned is None:
                raise DiscoveryConflictError("Opportunity was modified by another request")
            opportunity = transitioned
        else:
            opportunity.transition_to(OpportunityStatus.DISCOVERY)
            opportunity.touch()
            if not await self._opportunities.replace(tenant_id, opportunity, opportunity.version - 1):
                raise DiscoveryConflictError("Opportunity was modified by another request")
        session = DiscoverySession(opportunity_id=opportunity.id, workspace_id=opportunity.workspace_id or "", created_by=subject)
        await self._repository.insert_session(tenant_id, session)
        return session

    async def get(self, session_id: str, tenant_id: str, workspace_ids: set[str]) -> tuple[DiscoverySession, list[DiscoveryMessage]]:
        session = await self._get_session(session_id, tenant_id, workspace_ids)
        return session, await self._repository.list_messages(tenant_id, session.id)

    async def add_message(self, session_id: str, request: CreateDiscoveryMessageRequest, tenant_id: str, subject: str, workspace_ids: set[str]) -> DiscoveryMessage:
        session = await self._get_session(session_id, tenant_id, workspace_ids)
        if session.status is not DiscoverySessionStatus.ACTIVE:
            raise DiscoveryConflictError("Only active discovery sessions accept messages")
        for _ in range(3):
            message = DiscoveryMessage(
                session_id=session.id,
                content=request.content,
                sequence=await self._repository.next_sequence(tenant_id, session.id),
                created_by=subject,
            )
            try:
                await self._repository.insert_message(tenant_id, session.workspace_id, message)
                return message
            except DuplicateKeyError:
                continue
        raise DiscoveryConflictError("Could not allocate a unique message sequence")

    async def update_context(self, session_id: str, request: UpdateDiscoveryContextRequest, tenant_id: str, workspace_ids: set[str]) -> DiscoverySession:
        session = await self._get_session(session_id, tenant_id, workspace_ids)
        expected_version = request.expected_version
        data = request.model_dump(exclude={"expected_version"})
        session.update_context(DiscoveryContext(**data), expected_version)
        if not await self._repository.replace_session(tenant_id, session, expected_version):
            raise DiscoveryConflictError("Discovery session was modified by another request")
        return session

    async def complete(self, session_id: str, tenant_id: str, workspace_ids: set[str]) -> DiscoverySession:
        session = await self._get_session(session_id, tenant_id, workspace_ids)
        expected_version = session.version
        session.transition_to(DiscoverySessionStatus.COMPLETED)
        session.version += 1
        session.updated_at = datetime.now(UTC)
        if not await self._repository.replace_session(tenant_id, session, expected_version):
            raise DiscoveryConflictError("Discovery session was modified by another request")
        return session

    async def _get_session(self, session_id: str, tenant_id: str, workspace_ids: set[str]) -> DiscoverySession:
        session = await self._repository.find_session(tenant_id, session_id)
        if session is None:
            raise DiscoveryNotFoundError("Discovery session not found")
        if session.workspace_id not in workspace_ids:
            raise DiscoveryAccessError("Workspace access denied")
        return session

    @staticmethod
    def _check_opportunity(opportunity: object | None, workspace_ids: set[str]) -> None:
        if opportunity is None:
            raise DiscoveryNotFoundError("Opportunity not found")
        if getattr(opportunity, "workspace_id", None) not in workspace_ids:
            raise DiscoveryAccessError("Workspace access denied")