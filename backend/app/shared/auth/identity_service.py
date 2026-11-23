import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from pymongo.errors import DuplicateKeyError

from ...config.settings import Settings
from .auth_model import IdentityClaims, UserRole
from .identity_repository import IdentityRepository, utc_now
from .oidc import OidcIssuedToken, OidcTokenIssuer
from .identity_schemas import (
    ConsumerCredentialsResponse,
    ConsumerResponse,
    CreateConsumerRequest,
    CreateUserRequest,
    TokenResponse,
    UserResponse,
)


class IdentityConflictError(Exception):
    """Raised when an identity resource already exists in the tenant."""


def _hash_secret(secret: str, salt: str) -> str:
    return hashlib.scrypt(
        secret.encode(),
        salt=salt.encode(),
        n=2**14,
        r=8,
        p=1,
    ).hex()


def _new_secret() -> str:
    return secrets.token_urlsafe(48)


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class IdentityService:
    def __init__(self, repository: IdentityRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings
        self._token_issuer = OidcTokenIssuer(settings)

    async def create_user(
        self,
        request: CreateUserRequest,
        principal: IdentityClaims,
    ) -> UserResponse:
        self._validate_workspaces(request.workspace_ids, principal)
        now = utc_now()
        document = {
            "id": str(uuid4()),
            "username": request.username.lower(),
            "tenant_id": principal.tenant_id,
            "roles": [role.value for role in request.roles],
            "workspace_ids": sorted(request.workspace_ids),
            "password_salt": secrets.token_hex(16),
            "created_at": now,
            "active": True,
        }
        document["password_hash"] = _hash_secret(request.password, document["password_salt"])
        try:
            await self._repository.insert_user(document)
        except DuplicateKeyError as exc:
            raise IdentityConflictError("Username already exists") from exc
        return UserResponse.model_validate(document)

    async def create_consumer(
        self,
        request: CreateConsumerRequest,
        principal: IdentityClaims,
    ) -> ConsumerCredentialsResponse:
        self._validate_workspaces(request.workspace_ids, principal)
        client_secret = _new_secret()
        salt = secrets.token_hex(16)
        now = utc_now()
        document = {
            "id": str(uuid4()),
            "name": request.name,
            "tenant_id": principal.tenant_id,
            "client_id": f"fluxium_{secrets.token_urlsafe(18)}",
            "secret_salt": salt,
            "secret_hash": _hash_secret(client_secret, salt),
            "roles": [role.value for role in request.roles],
            "workspace_ids": sorted(request.workspace_ids),
            "created_at": now,
            "active": True,
        }
        try:
            await self._repository.insert_consumer(document)
        except DuplicateKeyError as exc:
            raise IdentityConflictError("Consumer already exists") from exc
        return ConsumerCredentialsResponse(
            **ConsumerResponse.model_validate(document).model_dump(),
            client_secret=client_secret,
        )

    async def rotate_consumer_credentials(
        self,
        client_id: str,
        principal: IdentityClaims,
    ) -> ConsumerCredentialsResponse:
        document = await self._repository.find_consumer_by_client_id(client_id)
        if document is None or document["tenant_id"] != principal.tenant_id:
            raise LookupError("Consumer not found")
        client_secret = _new_secret()
        salt = secrets.token_hex(16)
        document["secret_salt"] = salt
        document["secret_hash"] = _hash_secret(client_secret, salt)
        await self._repository.replace_consumer(client_id, document)
        return ConsumerCredentialsResponse(
            **ConsumerResponse.model_validate(document).model_dump(),
            client_secret=client_secret,
        )

    async def issue_consumer_token(
        self,
        client_id: str,
        client_secret: str,
        expires: int,
        tenant_id: str | None = None,
        scope: str = "openid",
    ) -> TokenResponse:
        issued = await self.issue_consumer_oidc_token(
            client_id,
            client_secret,
            expires,
            tenant_id=tenant_id,
            scope=scope,
        )
        return TokenResponse(access_token=issued.access_token, expires_in_seconds=expires)

    async def issue_consumer_oidc_token(
        self,
        client_id: str,
        client_secret: str,
        expires: int,
        tenant_id: str | None = None,
        scope: str = "openid",
    ) -> OidcIssuedToken:
        document = await self._repository.find_consumer_by_client_id(client_id, tenant_id)
        if document is None:
            raise PermissionError("Invalid consumer credentials")
        candidate = _hash_secret(client_secret, document["secret_salt"])
        if not hmac.compare_digest(candidate, document["secret_hash"]):
            raise PermissionError("Invalid consumer credentials")
        return self._token_issuer.issue(
            subject=f"consumer:{document['id']}",
            tenant_id=document["tenant_id"],
            workspace_ids=self._resolve_workspace_ids(document["workspace_ids"]),
            roles=document["roles"],
            expires=expires,
            scope=scope,
            preferred_username=f"service-account-{client_id}",
            extra_claims={
                "consumer_id": document["id"],
                "client_id": client_id,
                "consumer_name": document["name"],
            },
        )

    async def issue_user_token(
        self,
        username: str,
        password: str,
        tenant_id: str,
        expires: int,
    ) -> TokenResponse:
        document = await self._repository.find_user(username, tenant_id)
        if document is None:
            raise PermissionError("Invalid user credentials")
        candidate = _hash_secret(password, document["password_salt"])
        if not hmac.compare_digest(candidate, document["password_hash"]):
            raise PermissionError("Invalid user credentials")
        response = self._issue_token(
            subject=f"user:{document['id']}",
            tenant_id=document["tenant_id"],
            workspace_ids=self._resolve_workspace_ids(document["workspace_ids"]),
            roles=document["roles"],
            expires=expires,
        )
        return await self._with_refresh_token(response, document, expires)

    async def refresh_user_token(self, refresh_token: str, expires: int) -> TokenResponse:
        issued = await self.refresh_user_oidc_token(refresh_token, expires)
        return TokenResponse(
            access_token=issued.access_token,
            expires_in_seconds=expires,
            refresh_token=issued.refresh_token,
            refresh_expires_in_seconds=issued.refresh_expires_in,
        )

    async def refresh_user_oidc_token(
        self,
        refresh_token: str,
        expires: int,
        tenant_id: str | None = None,
        scope: str = "openid",
    ) -> OidcIssuedToken:
        document = await self._repository.consume_refresh_token(
            _hash_refresh_token(refresh_token),
            utc_now(),
            tenant_id,
        )
        if document is None:
            raise PermissionError("Invalid or expired refresh token")
        issued = self._token_issuer.issue(
            subject=document["subject"],
            tenant_id=document["tenant_id"],
            workspace_ids=self._resolve_workspace_ids(document["workspace_ids"]),
            roles=document["roles"],
            expires=expires,
            scope=scope,
        )
        response = TokenResponse(access_token=issued.access_token, expires_in_seconds=expires)
        response = await self._with_refresh_token(response, document, expires)
        return OidcIssuedToken(
            access_token=issued.access_token,
            id_token=issued.id_token,
            claims=issued.claims,
            refresh_token=response.refresh_token,
            refresh_expires_in=response.refresh_expires_in_seconds,
        )

    async def _with_refresh_token(
        self,
        response: TokenResponse,
        identity: dict,
        expires: int,
    ) -> TokenResponse:
        refresh_ttl = getattr(self._settings, "identity_refresh_token_ttl_seconds", 0)
        if refresh_ttl <= 0:
            return response
        raw_token = _new_secret()
        await self._repository.insert_refresh_token(
            {
                "token_hash": _hash_refresh_token(raw_token),
                "subject": identity.get("subject") or f"user:{identity['id']}",
                "tenant_id": identity["tenant_id"],
                "workspace_ids": identity["workspace_ids"],
                "roles": identity["roles"],
                "created_at": utc_now(),
                "expires_at": utc_now() + timedelta(seconds=refresh_ttl),
                "used_at": None,
                "revoked_at": None,
            }
        )
        return response.model_copy(
            update={
                "refresh_token": raw_token,
                "refresh_expires_in_seconds": refresh_ttl,
            }
        )

    def _issue_token(
        self,
        *,
        subject: str,
        tenant_id: str,
        workspace_ids: list[str],
        roles: list[str],
        expires: int,
    ) -> TokenResponse:
        issued = self._token_issuer.issue(
            subject=subject,
            tenant_id=tenant_id,
            workspace_ids=workspace_ids,
            roles=roles,
            expires=expires,
        )
        return TokenResponse(access_token=issued.access_token, expires_in_seconds=expires)

    def _resolve_workspace_ids(self, workspace_ids: list[str]) -> list[str]:
        if workspace_ids:
            return workspace_ids
        default_workspace_id = getattr(self._settings, "default_workspace_id", "")
        return [default_workspace_id] if default_workspace_id else []

    @staticmethod
    def _validate_workspaces(workspace_ids: set[str], principal: IdentityClaims) -> None:
        if not workspace_ids.issubset(principal.workspace_ids):
            raise PermissionError("Workspace access denied")