from typing import Protocol

from .auth_model import IdentityClaims
from .identity_schemas import (
    ConsumerCredentialsResponse,
    CreateConsumerRequest,
    CreateUserRequest,
    TokenResponse,
    UserResponse,
)
from .oidc import OidcIssuedToken


class IdentityProvisioningPort(Protocol):
    async def create_user(
        self,
        request: CreateUserRequest,
        principal: IdentityClaims,
    ) -> UserResponse:
        ...

    async def create_consumer(
        self,
        request: CreateConsumerRequest,
        principal: IdentityClaims,
    ) -> ConsumerCredentialsResponse:
        ...

    async def rotate_consumer_credentials(
        self,
        client_id: str,
        principal: IdentityClaims,
    ) -> ConsumerCredentialsResponse:
        ...

    async def issue_consumer_token(
        self,
        client_id: str,
        client_secret: str,
        expires: int,
        tenant_id: str | None = None,
        scope: str = "openid",
    ) -> TokenResponse:
        ...

    async def issue_consumer_oidc_token(
        self,
        client_id: str,
        client_secret: str,
        expires: int,
        tenant_id: str | None = None,
        scope: str = "openid",
    ) -> OidcIssuedToken:
        ...

    async def issue_user_token(
        self,
        username: str,
        password: str,
        tenant_id: str,
        expires: int,
    ) -> TokenResponse:
        ...

    async def refresh_user_token(self, refresh_token: str, expires: int) -> TokenResponse:
        ...

    async def refresh_user_oidc_token(
        self,
        refresh_token: str,
        expires: int,
        tenant_id: str | None = None,
        scope: str = "openid",
    ) -> OidcIssuedToken:
        ...