from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..domain.enums import DiscoveryMessageRole, DiscoverySessionStatus


class DiscoveryContextResponse(BaseModel):
    affected_audience: str | None = None
    observed_problem: str | None = None
    occurrence: str | None = None
    reported_impact: str | None = None
    mentioned_evidence: str | None = None
    expected_outcome: str | None = None
    measurement: str | None = None
    open_questions: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DiscoveryMessageResponse(BaseModel):
    id: str
    role: DiscoveryMessageRole
    content: str
    sequence: int
    created_by: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiscoverySessionResponse(BaseModel):
    id: str
    opportunity_id: str
    workspace_id: str
    status: DiscoverySessionStatus
    mode: str
    context: DiscoveryContextResponse
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    messages: list[DiscoveryMessageResponse] = []

    model_config = ConfigDict(from_attributes=True)