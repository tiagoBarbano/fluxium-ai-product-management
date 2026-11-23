from typing import Any, Protocol

from pymongo import ASCENDING
from pymongo.asynchronous.collection import AsyncCollection

from .domain.entities import Workspace


class WorkspaceRepository(Protocol):
    async def ensure_indexes(self) -> None: ...
    async def insert(self, workspace: Workspace) -> None: ...


class MongoWorkspaceRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("name", ASCENDING)],
            unique=True,
            name="uq_workspaces_tenant_name",
        )

    async def insert(self, workspace: Workspace) -> None:
        await self._collection.insert_one(self._to_document(workspace))

    @staticmethod
    def _to_document(workspace: Workspace) -> dict[str, Any]:
        return {
            "id": workspace.id,
            "tenant_id": workspace.tenant_id,
            "name": workspace.name,
            "description": workspace.description,
            "status": workspace.status,
            "created_by": workspace.created_by,
            "created_at": workspace.created_at,
        }