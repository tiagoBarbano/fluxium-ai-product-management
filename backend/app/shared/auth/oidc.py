from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
from typing import Any
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives import serialization

from ...config.settings import Settings


@dataclass(frozen=True, slots=True)
class OidcIssuedToken:
    access_token: str
    id_token: str
    claims: dict[str, Any]
    refresh_token: str | None = None
    refresh_expires_in: int = 0


class OidcTokenIssuer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def issue(
        self,
        *,
        subject: str,
        tenant_id: str,
        workspace_ids: list[str],
        roles: list[str],
        expires: int,
        audience: str | list[str] | None = None,
        scope: str = "openid",
        preferred_username: str | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> OidcIssuedToken:
        algorithm = self._algorithm()
        signing_key = self._signing_key()

        now = datetime.now(UTC)
        resolved_audience = audience or self._settings.identity_jwt_audience or "fluxium-api"
        claims: dict[str, Any] = {
            "exp": now + timedelta(seconds=expires),
            "iat": now,
            "jti": str(uuid4()),
            "iss": self._settings.identity_jwt_issuer or "fluxium-internal",
            "aud": resolved_audience,
            "sub": subject,
            "typ": "Bearer",
            "azp": preferred_username or subject,
            "scope": scope,
            "tenant_id": tenant_id,
            "workspace_ids": workspace_ids,
            "roles": roles,
            "groups": roles,
        }
        if preferred_username:
            claims["preferred_username"] = preferred_username
        if extra_claims:
            protected = {
                "exp", "iat", "jti", "iss", "aud", "sub", "typ", "azp",
                "scope", "tenant_id", "workspace_ids", "roles", "groups",
            }
            claims.update({key: value for key, value in extra_claims.items() if key not in protected})

        headers = {"kid": getattr(self._settings, "identity_jwt_key_id", "fluxium-internal")}
        access_token = jwt.encode(claims, signing_key, algorithm=algorithm, headers=headers)
        id_claims = {**claims, "typ": "ID", "aud": [preferred_username or subject]}
        id_token = jwt.encode(id_claims, signing_key, algorithm=algorithm, headers=headers)
        return OidcIssuedToken(access_token=access_token, id_token=id_token, claims=claims)

    def public_jwk(self) -> dict[str, Any] | None:
        if self._algorithm() != "RS256":
            return None
        public_key = self._public_key()
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(public_key))
        jwk.update(
            {
                "kid": self._settings.identity_jwt_key_id,
                "use": "sig",
                "alg": "RS256",
            }
        )
        return jwk

    def _algorithm(self) -> str:
        algorithm = getattr(self._settings, "identity_jwt_algorithm", "HS256").upper()
        if algorithm not in {"HS256", "RS256"}:
            raise RuntimeError("Unsupported identity JWT algorithm")
        return algorithm

    def _signing_key(self) -> Any:
        if self._algorithm() == "HS256":
            if not self._settings.identity_jwt_secret:
                raise RuntimeError("Identity provider is not configured")
            return self._settings.identity_jwt_secret
        private_key = getattr(self._settings, "identity_jwt_private_key", "")
        if not private_key:
            raise RuntimeError("RS256 private key is not configured")
        return serialization.load_pem_private_key(
            private_key.replace("\\n", "\n").encode(),
            password=None,
        )

    def _public_key(self) -> Any:
        public_key = getattr(self._settings, "identity_jwt_public_key", "")
        if public_key:
            return serialization.load_pem_public_key(public_key.replace("\\n", "\n").encode())
        private_key = self._signing_key()
        return private_key.public_key()