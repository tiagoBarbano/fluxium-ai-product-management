from pydantic import BaseModel, ConfigDict, Field

from ..domain.enums import EvidenceOrigin, EvidenceType


class CreateEvidenceRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    type: EvidenceType
    origin: EvidenceOrigin
    description: str = Field(min_length=1, max_length=5_000)
    problem_id: str | None = Field(default=None, min_length=1, max_length=100)
    hypothesis_id: str | None = Field(default=None, min_length=1, max_length=100)
    source: str | None = Field(default=None, max_length=500)
    reference: str | None = Field(default=None, max_length=2_000)