from datetime import datetime

from pydantic import BaseModel

from ..domain.entities import Hypothesis
from ..domain.enums import HypothesisStatus


class HypothesisResponse(BaseModel):
    id: str
    workspace_id: str
    opportunity_id: str
    statement: str
    expected_behavior: str
    expected_outcome: str
    evidence_ids: list[str]
    confidence: float
    status: HypothesisStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    version: int

    @classmethod
    def from_entity(cls, hypothesis: Hypothesis) -> "HypothesisResponse":
        return cls.model_validate(hypothesis, from_attributes=True)