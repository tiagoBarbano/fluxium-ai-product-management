from datetime import datetime

from pydantic import BaseModel

from ..domain.entities import Initiative
from ..domain.enums import InitiativeStatus


class InitiativeResponse(BaseModel):
    id: str
    workspace_id: str
    product_id: str
    opportunity_id: str
    problem_id: str | None
    title: str
    objective: str
    hypothesis_ids: list[str]
    objective_ids: list[str]
    evidence_ids: list[str]
    scope: str
    out_of_scope: str | None
    status: InitiativeStatus
    readiness_score: float | None
    readiness_confidence: float | None
    delivery_confidence: float | None
    outcome_confidence: float | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    version: int

    @classmethod
    def from_entity(cls, initiative: Initiative) -> "InitiativeResponse":
        return cls.model_validate(initiative, from_attributes=True)