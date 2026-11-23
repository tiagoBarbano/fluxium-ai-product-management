from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .auth_model import UserRole


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    password: str = Field(min_length=12, max_length=256)
    roles: set[UserRole] = Field(default_factory=lambda: {UserRole.CONTRIBUTOR})
    workspace_ids: set[str] = Field(min_length=1)


class UserResponse(BaseModel):
    id: str
    username: str
    tenant_id: str
    roles: set[UserRole]
    workspace_ids: set[str]
    created_at: datetime


class CreateConsumerRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    roles: set[UserRole] = Field(default_factory=lambda: {UserRole.CONTRIBUTOR})
    workspace_ids: set[str] = Field(min_length=1)


class ConsumerResponse(BaseModel):
    id: str
    name: str
    tenant_id: str
    client_id: str
    roles: set[UserRole]
    workspace_ids: set[str]
    created_at: datetime


class ConsumerCredentialsResponse(ConsumerResponse):
    client_secret: str


class ConsumerTokenRequest(BaseModel):
    client_id: str = Field(min_length=8, max_length=128)
    client_secret: str = Field(min_length=1, max_length=256)
    expires_in_seconds: int = Field(default=3600, ge=60, le=86400)


class UserTokenRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=1, max_length=256)
    tenant_id: str = Field(min_length=1, max_length=120)
    expires_in_seconds: int = Field(default=3600, ge=60, le=86400)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    refresh_token: str | None = None
    refresh_expires_in_seconds: int = 0


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)
    expires_in_seconds: int = Field(default=3600, ge=60, le=86400)


class OidcTokenResponse(BaseModel):
    access_token: str
    expires_in: int
    refresh_expires_in: int = 0
    token_type: str = "Bearer"
    id_token: str
    scope: str = "openid"
    refresh_token: str | None = None


class OidcDiscoveryResponse(BaseModel):
    issuer: str
    token_endpoint: str
    grant_types_supported: list[str]
    response_types_supported: list[str]
    subject_types_supported: list[str]
    id_token_signing_alg_values_supported: list[str]
    scopes_supported: list[str]
    jwks_uri: str


class IdentityErrorResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    detail: Any