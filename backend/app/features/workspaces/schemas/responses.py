from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..domain.entities import Workspace


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    description: str | None
    status: str
    created_by: str
    created_at: datetime

    @classmethod
    def from_entity(cls, workspace: Workspace) -> "WorkspaceResponse":
        return cls.model_validate(workspace)