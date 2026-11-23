from datetime import datetime

from pydantic import BaseModel, Field

from ..domain.entities import Proposal
from ..domain.enums import ProposalStatus


class ProposalResponse(BaseModel):
    id: str
    initiative_id: str
    assessment_id: str
    changes: dict[str, object]
    status: ProposalStatus
    created_by: str
    decided_by: str | None
    decision_reason: str | None
    created_at: datetime
    decided_at: datetime | None
    expected_initiative_version: int
    business_document: dict[str, object] = Field(default_factory=dict)

    @classmethod
    def from_entity(cls, proposal: Proposal) -> "ProposalResponse":
        return cls.model_validate(proposal, from_attributes=True)