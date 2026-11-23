from collections.abc import Iterable
from functools import lru_cache
from typing import Any, Protocol

import jwt
from cryptography.hazmat.primitives import serialization
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...config.settings import Settings, get_settings
from .auth_model import IdentityClaims, UserRole


security = HTTPBearer(auto_error=False)
security_dependency = Depends(security)


class TokenVerifier(Protocol):
    def verify(self, token: str) -> IdentityClaims:
        ...


def _unauthorized(detail: str = "Invalid authentication token") -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _claim_values(value: Any) -> set[str]:
    if isinstance(value, str):
        return {item.strip() for item in value.replace(",", " ").split() if item.strip()}
    if isinstance(value, Iterable) and not isinstance(value, (bytes, dict)):
        return {str(item).strip() for item in value if str(item).strip()}
    return set()


def _normalize_claims(payload: dict[str, Any]) -> IdentityClaims:
    subject = str(payload.get("sub") or "").strip()
    tenant_id = str(payload.get("tenant_id") or payload.get("tenantId") or "").strip()
    roles = _claim_values(payload.get("roles"))
    roles.update(_claim_values((payload.get("realm_access") or {}).get("roles")))
    workspace_ids = _claim_values(payload.get("workspace_ids"))
    workspace_ids.update(_claim_values(payload.get("workspaceIds")))
    workspace_id = str(payload.get("workspace_id") or payload.get("workspaceId") or "").strip()
    if workspace_id:
        workspace_ids.add(workspace_id)

    try:
        normalized_roles = {UserRole(role.upper()) for role in roles}
        return IdentityClaims(
            subject=subject,
            tenant_id=tenant_id,
            workspace_ids=frozenset(workspace_ids),
            roles=frozenset(normalized_roles),
            raw=payload,
        )
    except ValueError as exc:
        raise _unauthorized("Token contains an unsupported role") from exc


class JwtTokenVerifier:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def verify(self, token: str) -> IdentityClaims:
        try:
            algorithm = self._settings.identity_jwt_algorithm.upper()
            if algorithm == "RS256":
                if not self._settings.identity_jwt_public_key:
                    raise HTTPException(status_code=503, detail="Identity public key is not configured")
                key = serialization.load_pem_public_key(
                    self._settings.identity_jwt_public_key.replace("\\n", "\n").encode()
                )
            else:
                if not self._settings.identity_jwt_secret:
                    raise HTTPException(status_code=503, detail="Identity provider is not configured")
                key = self._settings.identity_jwt_secret
            payload = jwt.decode(
                token,
                key,
                algorithms=[algorithm],
                audience=self._settings.identity_jwt_audience or None,
                issuer=self._settings.identity_jwt_issuer or None,
                options={
                    "require": ["sub", "exp"],
                    "verify_aud": bool(self._settings.identity_jwt_audience),
                    "verify_iss": bool(self._settings.identity_jwt_issuer),
                },
            )
            return _normalize_claims(payload)
        except jwt.PyJWTError as exc:
            raise _unauthorized() from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise _unauthorized("Token is missing required identity claims") from exc


@lru_cache(maxsize=1)
def get_token_verifier() -> JwtTokenVerifier:
    return JwtTokenVerifier(get_settings())


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = security_dependency,
) -> IdentityClaims:
    if credentials is None:
        raise _unauthorized("Bearer token is required")
    return get_token_verifier().verify(credentials.credentials)
