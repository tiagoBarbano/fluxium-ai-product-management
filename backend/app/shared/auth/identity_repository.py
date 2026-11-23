from datetime import UTC, datetime
from typing import Any, Protocol

from pymongo import ASCENDING, ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection


class IdentityRepository(Protocol):
    async def insert_user(self, document: dict[str, Any]) -> None:
        ...

    async def insert_consumer(self, document: dict[str, Any]) -> None:
        ...

    async def find_user(self, username: str, tenant_id: str) -> dict[str, Any] | None:
        ...

    async def find_consumer_by_client_id(
        self,
        client_id: str,
        tenant_id: str | None = None,
    ) -> dict[str, Any] | None:
        ...

    async def replace_consumer(self, client_id: str, document: dict[str, Any]) -> None:
        ...

    async def add_workspace_to_user(self, subject: str, tenant_id: str, workspace_id: str) -> bool:
        ...

    async def insert_refresh_token(self, document: dict[str, Any]) -> None:
        ...

    async def consume_refresh_token(
        self,
        token_hash: str,
        now: datetime,
        tenant_id: str | None = None,
    ) -> dict[str, Any] | None:
        ...


class MongoIdentityRepository:
    def __init__(
        self,
        users: AsyncCollection,
        consumers: AsyncCollection,
        refresh_tokens: AsyncCollection | None = None,
    ) -> None:
        self._users = users
        self._consumers = consumers
        self._refresh_tokens = refresh_tokens

    async def ensure_indexes(self) -> None:
        await self._users.create_index(
            [("tenant_id", ASCENDING), ("username", ASCENDING)],
            unique=True,
            name="uq_identity_users_tenant_username",
        )
        await self._consumers.create_index(
            [("tenant_id", ASCENDING), ("name", ASCENDING)],
            unique=True,
            name="uq_identity_consumers_tenant_name",
        )
        await self._consumers.create_index(
            [("client_id", ASCENDING)],
            unique=True,
            name="uq_identity_consumers_client_id",
        )
        if self._refresh_tokens is not None:
            await self._refresh_tokens.create_index(
                [("token_hash", ASCENDING)],
                unique=True,
                name="uq_identity_refresh_tokens_hash",
            )
            await self._refresh_tokens.create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="ttl_identity_refresh_tokens_expires_at",
            )

    async def insert_user(self, document: dict[str, Any]) -> None:
        await self._users.insert_one(document)

    async def insert_consumer(self, document: dict[str, Any]) -> None:
        await self._consumers.insert_one(document)

    async def find_user(self, username: str, tenant_id: str) -> dict[str, Any] | None:
        return await self._users.find_one(
            {"username": username.lower(), "tenant_id": tenant_id, "active": True}
        )

    async def find_consumer_by_client_id(
        self,
        client_id: str,
        tenant_id: str | None = None,
    ) -> dict[str, Any] | None:
        query = {"client_id": client_id, "active": True}
        if tenant_id:
            query["tenant_id"] = tenant_id
        return await self._consumers.find_one(query)

    async def replace_consumer(self, client_id: str, document: dict[str, Any]) -> None:
        await self._consumers.replace_one({"client_id": client_id}, document)

    async def add_workspace_to_user(self, subject: str, tenant_id: str, workspace_id: str) -> bool:
        if not subject.startswith("user:"):
            return False
        result = await self._users.update_one(
            {"id": subject.removeprefix("user:"), "tenant_id": tenant_id, "active": True},
            {"$addToSet": {"workspace_ids": workspace_id}},
        )
        if result.matched_count == 1 and self._refresh_tokens is not None:
            await self._refresh_tokens.update_many(
                {"subject": subject, "tenant_id": tenant_id, "revoked_at": None},
                {"$addToSet": {"workspace_ids": workspace_id}},
            )
        return result.modified_count == 1 or result.matched_count == 1

    async def insert_refresh_token(self, document: dict[str, Any]) -> None:
        if self._refresh_tokens is None:
            raise RuntimeError("Refresh token storage is not configured")
        await self._refresh_tokens.insert_one(document)

    async def consume_refresh_token(
        self,
        token_hash: str,
        now: datetime,
        tenant_id: str | None = None,
    ) -> dict[str, Any] | None:
        if self._refresh_tokens is None:
            raise RuntimeError("Refresh token storage is not configured")
        query: dict[str, Any] = {
            "token_hash": token_hash,
            "used_at": None,
            "revoked_at": None,
            "expires_at": {"$gt": now},
        }
        if tenant_id:
            query["tenant_id"] = tenant_id
        return await self._refresh_tokens.find_one_and_update(
            query,
            {"$set": {"used_at": now}},
            return_document=ReturnDocument.BEFORE,
        )


def utc_now() -> datetime:
    return datetime.now(UTC)