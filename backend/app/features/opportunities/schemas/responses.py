from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ..domain.enums import OpportunityStatus


class OpportunityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    title: str
    description: str
    objective_ids: list[str] = Field(default_factory=list)
    status: OpportunityStatus
    workspace_id: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    version: int