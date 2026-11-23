from dataclasses import asdict
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..domain.entities import BusinessPlan


class BusinessPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    initiative_id: str
    workspace_id: str
    rationale: str
    what: str | None
    why: str | None
    where: str | None
    when: str | None
    who: str | None
    how: str | None
    how_much: str | None
    metrics: list[str]
    risks: list[str]
    created_at: datetime
    updated_at: datetime
    version: int

    @classmethod
    def from_entity(cls, plan: BusinessPlan) -> "BusinessPlanResponse":
        data = asdict(plan)
        data["metrics"] = list(plan.metrics)
        data["risks"] = list(plan.risks)
        return cls.model_validate(data)