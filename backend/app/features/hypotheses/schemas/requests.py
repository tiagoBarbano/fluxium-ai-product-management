from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..domain.enums import HypothesisStatus


class CreateHypothesisRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    statement: str = Field(min_length=1, max_length=5_000)
    expected_behavior: str = Field(min_length=1, max_length=5_000)
    expected_outcome: str = Field(min_length=1, max_length=5_000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)
    confidence: float = Field(ge=0, le=1)


class UpdateHypothesisRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    expected_version: int = Field(gt=0)
    statement: str | None = Field(default=None, min_length=1, max_length=5_000)
    expected_behavior: str | None = Field(default=None, min_length=1, max_length=5_000)
    expected_outcome: str | None = Field(default=None, min_length=1, max_length=5_000)
    evidence_ids: list[str] | None = Field(default=None, max_length=100)
    confidence: float | None = Field(default=None, ge=0, le=1)
    status: HypothesisStatus | None = None

    @model_validator(mode="after")
    def require_change(self) -> "UpdateHypothesisRequest":
        fields = ("statement", "expected_behavior", "expected_outcome", "evidence_ids", "confidence", "status")
        if all(getattr(self, field) is None for field in fields):
            raise ValueError("At least one Hypothesis field must be provided")
        return self