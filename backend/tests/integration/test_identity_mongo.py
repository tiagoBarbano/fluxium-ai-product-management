import os
from uuid import uuid4

import jwt
import pytest
from pymongo import AsyncMongoClient

from app.config.settings import Settings
from app.shared.auth.auth_model import IdentityClaims, UserRole
from app.shared.auth.identity_repository import MongoIdentityRepository
from app.shared.auth.identity_schemas import CreateConsumerRequest, CreateUserRequest
from app.shared.auth.identity_service import IdentityService


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("FLUXIUM_RUN_MONGO_INTEGRATION") != "1",
    reason="Set FLUXIUM_RUN_MONGO_INTEGRATION=1 to run MongoDB integration tests",
)
@pytest.mark.asyncio
async def test_identity_cycle_persists_and_rotates_against_mongodb() -> None:
    database_name = f"fluxium_identity_test_{uuid4().hex}"
    client = AsyncMongoClient(
        os.getenv("FLUXIUM_MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
    )
    database = client[database_name]
    repository = MongoIdentityRepository(
        database["identity_users"],
        database["identity_consumers"],
    )
    service = IdentityService(
        repository,
        Settings(
            mongo_database=database_name,
            identity_jwt_secret="integration-secret-with-at-least-32-bytes",
        ),
    )
    principal = IdentityClaims(
        subject="integration-admin",
        tenant_id="tenant-integration",
        workspace_ids={"workspace-integration"},
        roles={UserRole.ADMIN},
    )

    try:
        await repository.ensure_indexes()
        user = await service.create_user(
            CreateUserRequest(
                username=f"user-{uuid4().hex[:8]}",
                password="integration-password",
                workspace_ids={"workspace-integration"},
            ),
            principal,
        )
        consumer = await service.create_consumer(
            CreateConsumerRequest(
                name=f"consumer-{uuid4().hex[:8]}",
                workspace_ids={"workspace-integration"},
            ),
            principal,
        )

        stored_user = await database["identity_users"].find_one({"id": user.id})
        stored_consumer = await database["identity_consumers"].find_one({"id": consumer.id})
        assert stored_user is not None
        assert stored_consumer is not None
        assert "password" not in stored_user
        assert "client_secret" not in stored_consumer

        user_token = await service.issue_user_token(
            user.username,
            "integration-password",
            principal.tenant_id,
            3600,
        )
        consumer_token = await service.issue_consumer_token(
            consumer.client_id,
            consumer.client_secret,
            3600,
        )
        assert jwt.decode(user_token.access_token, options={"verify_signature": False})["tenant_id"] == principal.tenant_id
        assert jwt.decode(consumer_token.access_token, options={"verify_signature": False})["tenant_id"] == principal.tenant_id

        rotated = await service.rotate_consumer_credentials(consumer.client_id, principal)
        with pytest.raises(PermissionError):
            await service.issue_consumer_token(consumer.client_id, consumer.client_secret, 3600)
        assert rotated.client_secret != consumer.client_secret
    finally:
        await client.drop_database(database_name)
        await client.close()