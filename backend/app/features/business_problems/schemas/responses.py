from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..domain.entities import BusinessProblem
from ..domain.enums import BusinessProblemStatus


class BusinessProblemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    product_id: str
    opportunity_id: str
    description: str
    audience: str
    reported_impact: str
    estimated_impact: str | None
    status: BusinessProblemStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    version: int

    @classmethod
    def from_entity(cls, problem: BusinessProblem) -> "BusinessProblemResponse":
        return cls.model_validate(problem, from_attributes=True)