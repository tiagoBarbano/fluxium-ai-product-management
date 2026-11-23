from datetime import UTC
from types import SimpleNamespace

import jwt
import pytest

from app.shared.auth.auth_model import IdentityClaims, UserRole
from app.shared.auth.identity_service import IdentityService
from app.shared.auth.identity_schemas import CreateConsumerRequest, CreateUserRequest


class FakeIdentityRepository:
    def __init__(self) -> None:
        self.users = []
        self.consumers = []
        self.refresh_tokens = []

    async def insert_user(self, document):
        self.users.append(document)

    async def insert_consumer(self, document):
        self.consumers.append(document)

    async def find_user(self, username, tenant_id):
        return next(
            (
                user
                for user in self.users
                if user["username"] == username.lower()
                and user["tenant_id"] == tenant_id
                and user["active"]
            ),
            None,
        )

    async def find_consumer_by_client_id(self, client_id, tenant_id=None):
        return next(
            (
                consumer
                for consumer in self.consumers
                if consumer["client_id"] == client_id
                and consumer["active"]
                and (tenant_id is None or consumer["tenant_id"] == tenant_id)
            ),
            None,
        )

    async def replace_consumer(self, client_id, document):
        for index, consumer in enumerate(self.consumers):
            if consumer["client_id"] == client_id:
                self.consumers[index] = document
                return

    async def insert_refresh_token(self, document):
        self.refresh_tokens.append(document)

    async def consume_refresh_token(self, token_hash, now, tenant_id=None):
        for token in self.refresh_tokens:
            if (
                token["token_hash"] == token_hash
                and (tenant_id is None or token["tenant_id"] == tenant_id)
                and token["used_at"] is None
                and token["revoked_at"] is None
                and token["expires_at"] > now
            ):
                token["used_at"] = now
                return {**token, "used_at": None}
        return None


@pytest.fixture
def principal():
    return IdentityClaims(
        subject="admin-1",
        tenant_id="tenant-1",
        workspace_ids={"workspace-1"},
        roles={UserRole.ADMIN},
    )


@pytest.fixture
def service():
    repository = FakeIdentityRepository()
    settings = SimpleNamespace(
        identity_jwt_secret="test-identity-secret-with-at-least-32-bytes",
        identity_jwt_issuer="",
        identity_jwt_audience="",
    )
    return IdentityService(repository, settings), repository


@pytest.mark.asyncio
async def test_consumer_credentials_issue_token_and_rotate(service, principal):
    identity_service, repository = service
    credentials = await identity_service.create_consumer(
        CreateConsumerRequest(name="Analytics", workspace_ids={"workspace-1"}),
        principal,
    )

    token = await identity_service.issue_consumer_token(
        credentials.client_id,
        credentials.client_secret,
        3600,
    )
    claims = jwt.decode(token.access_token, options={"verify_signature": False})
    assert claims["tenant_id"] == "tenant-1"
    assert claims["sub"].startswith("consumer:")

    rotated = await identity_service.rotate_consumer_credentials(credentials.client_id, principal)
    with pytest.raises(PermissionError):
        await identity_service.issue_consumer_token(credentials.client_id, credentials.client_secret, 3600)
    assert rotated.client_secret != credentials.client_secret
    assert len(repository.consumers) == 1


@pytest.mark.asyncio
async def test_user_password_is_hashed_and_token_can_be_issued(service, principal):
    identity_service, repository = service
    user = await identity_service.create_user(
        CreateUserRequest(
            username="alice",
            password="a-strong-password",
            workspace_ids={"workspace-1"},
        ),
        principal,
    )

    assert "password" not in repository.users[0]
    assert repository.users[0]["password_hash"] != "a-strong-password"
    token = await identity_service.issue_user_token("alice", "a-strong-password", "tenant-1", 3600)
    assert jwt.decode(token.access_token, options={"verify_signature": False})["sub"] == f"user:{user.id}"


@pytest.mark.asyncio
async def test_default_workspace_is_used_when_identity_has_no_workspace(service, principal):
    identity_service, repository = service
    identity_service._settings.default_workspace_id = "workspace-default"
    await identity_service.create_user(
        CreateUserRequest(
            username="alice",
            password="a-strong-password",
            workspace_ids={"workspace-1"},
        ),
        principal,
    )
    repository.users[0]["workspace_ids"] = []

    token = await identity_service.issue_user_token("alice", "a-strong-password", "tenant-1", 3600)

    claims = jwt.decode(token.access_token, options={"verify_signature": False})
    assert claims["workspace_ids"] == ["workspace-default"]


@pytest.mark.asyncio
async def test_identity_operations_cannot_escape_tenant(service, principal):
    identity_service, _ = service
    with pytest.raises(PermissionError):
        await identity_service.create_user(
            CreateUserRequest(username="alice", password="a-strong-password", workspace_ids={"other-workspace"}),
            principal,
        )


@pytest.mark.asyncio
async def test_user_refresh_token_is_hashed_rotated_and_single_use(service, principal):
    identity_service, repository = service
    identity_service._settings.identity_refresh_token_ttl_seconds = 3600
    await identity_service.create_user(
        CreateUserRequest(
            username="alice",
            password="a-strong-password",
            workspace_ids={"workspace-1"},
        ),
        principal,
    )

    issued = await identity_service.issue_user_token(
        "alice", "a-strong-password", "tenant-1", 3600
    )
    assert issued.refresh_token is not None
    assert issued.refresh_token not in str(repository.refresh_tokens)
    assert len(repository.refresh_tokens) == 1

    rotated = await identity_service.refresh_user_token(issued.refresh_token, 3600)
    assert rotated.refresh_token is not None
    assert rotated.refresh_token != issued.refresh_token
    assert len(repository.refresh_tokens) == 2

    with pytest.raises(PermissionError):
        await identity_service.refresh_user_token(issued.refresh_token, 3600)