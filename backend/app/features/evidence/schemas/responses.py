from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..domain.entities import Evidence
from ..domain.enums import EvidenceOrigin, EvidenceType


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    opportunity_id: str
    problem_id: str | None
    hypothesis_id: str | None
    type: EvidenceType
    origin: EvidenceOrigin
    description: str
    source: str | None
    reference: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, evidence: Evidence) -> "EvidenceResponse":
        return cls.model_validate(evidence, from_attributes=True)