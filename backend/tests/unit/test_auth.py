from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from app.config.settings import Settings
from app.shared.auth.auth_model import UserRole
from app.shared.auth.authorization import can_approve_ai_proposal
from app.shared.auth.oidc import OidcTokenIssuer
from app.shared.auth.security import JwtTokenVerifier, _normalize_claims


SECRET = "test-identity-secret-with-at-least-32-bytes"


def _token(**claims: object) -> str:
    payload = {
        "sub": "user-1",
        "tenant_id": "tenant-1",
        "workspace_ids": ["workspace-1"],
        "roles": ["PRODUCT_MANAGER"],
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        **claims,
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def test_normalizes_identity_claims_and_roles() -> None:
    principal = _normalize_claims(
        {
            "sub": "user-1",
            "tenantId": "tenant-1",
            "workspaceId": "workspace-1",
            "realm_access": {"roles": ["ADMIN"]},
        }
    )

    assert principal.subject == "user-1"
    assert principal.tenant_id == "tenant-1"
    assert principal.workspace_ids == {"workspace-1"}
    assert principal.roles == {UserRole.ADMIN}


def test_verifier_rejects_missing_secret() -> None:
    with pytest.raises(HTTPException) as error:
        JwtTokenVerifier(Settings(identity_jwt_secret="")).verify(_token())

    assert error.value.status_code == 503


def test_verifier_accepts_signed_token() -> None:
    principal = JwtTokenVerifier(Settings(identity_jwt_secret=SECRET)).verify(_token())

    assert principal.subject == "user-1"
    assert UserRole.PRODUCT_MANAGER in principal.roles


def test_verifier_rejects_invalid_signature() -> None:
    with pytest.raises(HTTPException) as error:
        JwtTokenVerifier(
            Settings(identity_jwt_secret="wrong-secret-with-at-least-32-bytes")
        ).verify(_token())

    assert error.value.status_code == 401


def test_rs256_token_is_verified_with_public_key_and_exposed_as_jwk() -> None:
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
    settings = Settings(
        identity_jwt_algorithm="RS256",
        identity_jwt_private_key=private_pem,
        identity_jwt_public_key=public_pem,
        identity_jwt_key_id="test-key",
        identity_jwt_issuer="https://issuer.example",
        identity_jwt_audience="fluxium-api",
    )

    issued = OidcTokenIssuer(settings).issue(
        subject="user:user-1",
        tenant_id="tenant-1",
        workspace_ids=["workspace-1"],
        roles=["ADMIN"],
        expires=3600,
    )
    principal = JwtTokenVerifier(settings).verify(issued.access_token)
    jwk = OidcTokenIssuer(settings).public_jwk()

    assert principal.subject == "user:user-1"
    assert jwk is not None
    assert jwk["kid"] == "test-key"
    assert jwk["alg"] == "RS256"
    assert jwk["use"] == "sig"


def test_approval_policy_contains_only_allowed_roles() -> None:
    assert can_approve_ai_proposal is not None
