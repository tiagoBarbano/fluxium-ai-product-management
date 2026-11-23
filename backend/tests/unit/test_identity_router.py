from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import create_app
from app.shared.auth.auth_model import IdentityClaims, UserRole
from app.shared.auth.identity_router import get_identity_service
from app.shared.auth.identity_service import IdentityConflictError
from app.shared.auth.oidc import OidcIssuedToken
from app.shared.auth.security import get_current_principal


def _principal(role: UserRole) -> IdentityClaims:
    return IdentityClaims(
        subject="principal-1",
        tenant_id="tenant-1",
        workspace_ids={"workspace-1"},
        roles={role},
    )


def _user_response() -> dict[str, object]:
    return {
        "id": "user-1",
        "username": "alice",
        "tenant_id": "tenant-1",
        "roles": [UserRole.CONTRIBUTOR.value],
        "workspace_ids": ["workspace-1"],
        "created_at": datetime.now(UTC),
    }


class FakeIdentityService:
    async def create_user(self, request, principal):
        return _user_response()


class ConflictingIdentityService:
    async def create_user(self, request, principal):
        raise IdentityConflictError("Username already exists")


class OidcIdentityService:
    async def issue_consumer_oidc_token(self, client_id, client_secret, expires, tenant_id=None, scope="openid"):
        return OidcIssuedToken(
            access_token="access-token",
            id_token="id-token",
            claims={"scope": scope},
        )

    async def refresh_user_oidc_token(self, refresh_token, expires, tenant_id=None, scope="openid"):
        return OidcIssuedToken(
            access_token="refreshed-access-token",
            id_token="refreshed-id-token",
            claims={"scope": scope},
            refresh_token="rotated-refresh-token",
            refresh_expires_in=3600,
        )


def test_admin_can_create_user() -> None:
    application = create_app()
    application.dependency_overrides[get_current_principal] = lambda: _principal(UserRole.ADMIN)
    application.dependency_overrides[get_identity_service] = FakeIdentityService

    response = TestClient(application).post(
        "/api/v1/identity/users",
        json={
            "username": "alice",
            "password": "a-strong-password",
            "workspace_ids": ["workspace-1"],
        },
    )

    assert response.status_code == 201
    assert response.json()["tenant_id"] == "tenant-1"


def test_non_admin_cannot_create_user() -> None:
    application = create_app()
    application.dependency_overrides[get_current_principal] = lambda: _principal(UserRole.CONTRIBUTOR)

    response = TestClient(application).post(
        "/api/v1/identity/users",
        json={
            "username": "alice",
            "password": "a-strong-password",
            "workspace_ids": ["workspace-1"],
        },
    )

    assert response.status_code == 403
    assert response.headers["content-type"].startswith("application/problem+json")


def test_duplicate_user_returns_conflict() -> None:
    application = create_app()
    application.dependency_overrides[get_current_principal] = lambda: _principal(UserRole.ADMIN)
    application.dependency_overrides[get_identity_service] = ConflictingIdentityService

    response = TestClient(application).post(
        "/api/v1/identity/users",
        json={
            "username": "alice",
            "password": "a-strong-password",
            "workspace_ids": ["workspace-1"],
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Username already exists"


def test_oidc_discovery_exposes_internal_provider_contract() -> None:
    response = TestClient(create_app()).get(
        "/api/v1/auth/realms/tenant-1/.well-known/openid-configuration"
    )

    assert response.status_code == 200
    assert response.json()["grant_types_supported"] == ["client_credentials", "refresh_token"]
    assert response.json()["id_token_signing_alg_values_supported"] == ["HS256"]


def test_oidc_token_accepts_form_credentials_and_scope() -> None:
    application = create_app()
    application.dependency_overrides[get_identity_service] = OidcIdentityService

    response = TestClient(application).post(
        "/api/v1/auth/realms/tenant-1/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "client-1",
            "client_secret": "secret-1",
            "scope": "api.read",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "Bearer"
    assert response.json()["scope"] == "openid api.read"


def test_oidc_token_rotates_refresh_token() -> None:
    application = create_app()
    application.dependency_overrides[get_identity_service] = OidcIdentityService

    response = TestClient(application).post(
        "/api/v1/auth/realms/tenant-1/protocol/openid-connect/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": "opaque-refresh-token-value-1234567890",
        },
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "refreshed-access-token"
    assert response.json()["refresh_token"] == "rotated-refresh-token"
    assert response.json()["refresh_expires_in"] == 3600