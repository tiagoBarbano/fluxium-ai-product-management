from typing import Any, Protocol

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.collection import AsyncCollection

from .domain.entities import DiscoveryContext, DiscoveryMessage, DiscoverySession
from .domain.enums import DiscoveryMessageRole, DiscoverySessionStatus


class DiscoveryRepository(Protocol):
    async def ensure_indexes(self) -> None: ...
    async def insert_session(self, tenant_id: str, session: DiscoverySession) -> None: ...
    async def find_session(self, tenant_id: str, session_id: str) -> DiscoverySession | None: ...
    async def find_active_for_opportunity(self, tenant_id: str, opportunity_id: str) -> DiscoverySession | None: ...
    async def replace_session(self, tenant_id: str, session: DiscoverySession, expected_version: int) -> bool: ...
    async def insert_message(self, tenant_id: str, workspace_id: str, message: DiscoveryMessage) -> None: ...
    async def list_messages(self, tenant_id: str, session_id: str) -> list[DiscoveryMessage]: ...
    async def next_sequence(self, tenant_id: str, session_id: str) -> int: ...


class MongoDiscoveryRepository:
    def __init__(self, sessions: AsyncCollection, messages: AsyncCollection) -> None:
        self._sessions = sessions
        self._messages = messages

    async def ensure_indexes(self) -> None:
        await self._sessions.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("opportunity_id", ASCENDING), ("status", ASCENDING)],
            name="ix_discovery_sessions_scope",
        )
        await self._sessions.create_index(
            [("tenant_id", ASCENDING), ("opportunity_id", ASCENDING)],
            unique=True,
            partialFilterExpression={"status": {"$in": ["ACTIVE", "PAUSED"]}},
            name="ux_discovery_sessions_active_opportunity",
        )
        await self._messages.create_index(
            [("tenant_id", ASCENDING), ("session_id", ASCENDING), ("sequence", ASCENDING)],
            unique=True,
            name="ux_discovery_messages_sequence",
        )

    async def insert_session(self, tenant_id: str, session: DiscoverySession) -> None:
        await self._sessions.insert_one(self._session_document(tenant_id, session))

    async def find_session(self, tenant_id: str, session_id: str) -> DiscoverySession | None:
        document = await self._sessions.find_one({"tenant_id": tenant_id, "id": session_id})
        return self._session_from_document(document) if document else None

    async def find_active_for_opportunity(self, tenant_id: str, opportunity_id: str) -> DiscoverySession | None:
        document = await self._sessions.find_one(
            {"tenant_id": tenant_id, "opportunity_id": opportunity_id, "status": {"$in": ["ACTIVE", "PAUSED"]}},
            sort=[("created_at", DESCENDING)],
        )
        return self._session_from_document(document) if document else None

    async def replace_session(self, tenant_id: str, session: DiscoverySession, expected_version: int) -> bool:
        result = await self._sessions.replace_one(
            {"tenant_id": tenant_id, "id": session.id, "version": expected_version},
            self._session_document(tenant_id, session),
        )
        return result.modified_count == 1

    async def insert_message(self, tenant_id: str, workspace_id: str, message: DiscoveryMessage) -> None:
        await self._messages.insert_one({
            "id": message.id,
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
            "session_id": message.session_id,
            "role": message.role.value,
            "content": message.content,
            "sequence": message.sequence,
            "created_by": message.created_by,
            "created_at": message.created_at,
        })

    async def list_messages(self, tenant_id: str, session_id: str) -> list[DiscoveryMessage]:
        cursor = self._messages.find({"tenant_id": tenant_id, "session_id": session_id}, sort=[("sequence", ASCENDING)])
        return [self._message_from_document(document) async for document in cursor]

    async def next_sequence(self, tenant_id: str, session_id: str) -> int:
        document = await self._messages.find_one({"tenant_id": tenant_id, "session_id": session_id}, sort=[("sequence", DESCENDING)])
        return (document["sequence"] + 1) if document else 1

    @staticmethod
    def _session_document(tenant_id: str, session: DiscoverySession) -> dict[str, Any]:
        return {
            "id": session.id,
            "tenant_id": tenant_id,
            "workspace_id": session.workspace_id,
            "opportunity_id": session.opportunity_id,
            "status": session.status.value,
            "mode": session.mode,
            "context": {
                "affected_audience": session.context.affected_audience,
                "observed_problem": session.context.observed_problem,
                "occurrence": session.context.occurrence,
                "reported_impact": session.context.reported_impact,
                "mentioned_evidence": session.context.mentioned_evidence,
                "expected_outcome": session.context.expected_outcome,
                "measurement": session.context.measurement,
                "open_questions": session.context.open_questions,
            },
            "version": session.version,
            "created_by": session.created_by,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }

    @staticmethod
    def _session_from_document(document: dict[str, Any]) -> DiscoverySession:
        return DiscoverySession(
            id=document["id"], opportunity_id=document["opportunity_id"], workspace_id=document["workspace_id"],
            created_by=document["created_by"], status=DiscoverySessionStatus(document["status"]), mode=document["mode"],
            context=DiscoveryContext(**document.get("context", {})),
            version=document["version"], created_at=document["created_at"], updated_at=document["updated_at"],
        )

    @staticmethod
    def _message_from_document(document: dict[str, Any]) -> DiscoveryMessage:
        return DiscoveryMessage(
            id=document["id"], session_id=document["session_id"], content=document["content"], sequence=document["sequence"],
            role=DiscoveryMessageRole(document["role"]), created_by=document.get("created_by"), created_at=document["created_at"],
        )