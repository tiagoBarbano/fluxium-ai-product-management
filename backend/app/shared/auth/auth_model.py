from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    PRODUCT_MANAGER = "PRODUCT_MANAGER"
    CONTRIBUTOR = "CONTRIBUTOR"
    VIEWER = "VIEWER"


class IdentityClaims(BaseModel):
    model_config = ConfigDict(extra="allow")

    subject: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    workspace_ids: frozenset[str] = Field(default_factory=frozenset)
    roles: frozenset[UserRole] = Field(default_factory=frozenset)
    raw: dict[str, Any] = Field(default_factory=dict)


class WorkspaceScope(BaseModel):
    tenant_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
