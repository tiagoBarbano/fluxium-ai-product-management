import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app
from app.shared.auth.identity_router import get_identity_service
from app.shared.auth.oidc import OidcTokenIssuer
from app.shared.auth.security import JwtTokenVerifier


pytestmark = pytest.mark.integration


def _rsa_settings() -> Settings:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return Settings(
        identity_jwt_algorithm="RS256",
        identity_jwt_private_key=private_pem,
        identity_jwt_public_key=public_pem,
        identity_jwt_key_id="integration-key",
        identity_jwt_issuer="https://issuer.example",
        identity_jwt_audience="fluxium-api",
    )


class FakeOidcService:
    def __init__(self, settings: Settings) -> None:
        self._issuer = OidcTokenIssuer(settings)

    async def issue_consumer_oidc_token(
        self,
        client_id: str,
        client_secret: str,
        expires: int,
        tenant_id: str | None = None,
        scope: str = "openid",
    ):
        return self._issuer.issue(
            subject=f"consumer:{client_id}",
            tenant_id=tenant_id or "tenant-1",
            workspace_ids=["workspace-1"],
            roles=["CONTRIBUTOR"],
            expires=expires,
            scope=scope,
            preferred_username=f"service-account-{client_id}",
        )


def test_rs256_oidc_http_flow_exposes_jwks_and_validates_token(monkeypatch) -> None:
    settings = _rsa_settings()
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    monkeypatch.setattr("app.shared.auth.identity_router.get_settings", lambda: settings)

    application = create_app()
    application.dependency_overrides[get_identity_service] = lambda: FakeOidcService(settings)

    with TestClient(application) as client:
        discovery = client.get(
            "/api/v1/auth/realms/tenant-1/.well-known/openid-configuration"
        )
        jwks = client.get("/api/v1/auth/realms/tenant-1/.well-known/jwks.json")
        token_response = client.post(
            "/api/v1/auth/realms/tenant-1/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "client-1",
                "client_secret": "secret-1",
            },
        )

    assert discovery.status_code == 200
    assert discovery.json()["jwks_uri"].endswith("/.well-known/jwks.json")
    assert discovery.json()["id_token_signing_alg_values_supported"] == ["RS256"]
    assert jwks.status_code == 200
    assert jwks.json()["keys"][0]["kid"] == "integration-key"
    assert token_response.status_code == 200

    access_token = token_response.json()["access_token"]
    assert jwt.get_unverified_header(access_token)["kid"] == "integration-key"
    principal = JwtTokenVerifier(settings).verify(access_token)
    assert principal.tenant_id == "tenant-1"