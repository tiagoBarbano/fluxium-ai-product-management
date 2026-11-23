from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..domain.enums import InitiativeStatus


class CreateInitiativeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    objective: str = Field(min_length=1, max_length=5_000)
    scope: str = Field(min_length=1, max_length=5_000)
    product_id: str | None = Field(default=None, min_length=1, max_length=100)
    problem_id: str | None = Field(default=None, min_length=1, max_length=100)
    hypothesis_ids: list[str] = Field(default_factory=list, max_length=100)
    objective_ids: list[str] = Field(default_factory=list, max_length=100)
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)
    out_of_scope: str | None = Field(default=None, max_length=5_000)
    readiness_score: float | None = Field(default=None, ge=0, le=1)
    readiness_confidence: float | None = Field(default=None, ge=0, le=1)
    delivery_confidence: float | None = Field(default=None, ge=0, le=1)
    outcome_confidence: float | None = Field(default=None, ge=0, le=1)


class UpdateInitiativeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    expected_version: int = Field(gt=0)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    objective: str | None = Field(default=None, min_length=1, max_length=5_000)
    scope: str | None = Field(default=None, min_length=1, max_length=5_000)
    problem_id: str | None = Field(default=None, min_length=1, max_length=100)
    hypothesis_ids: list[str] | None = Field(default=None, max_length=100)
    objective_ids: list[str] | None = Field(default=None, max_length=100)
    evidence_ids: list[str] | None = Field(default=None, max_length=100)
    out_of_scope: str | None = Field(default=None, max_length=5_000)
    readiness_score: float | None = Field(default=None, ge=0, le=1)
    readiness_confidence: float | None = Field(default=None, ge=0, le=1)
    delivery_confidence: float | None = Field(default=None, ge=0, le=1)
    outcome_confidence: float | None = Field(default=None, ge=0, le=1)
    status: InitiativeStatus | None = None

    @model_validator(mode="after")
    def require_change(self) -> "UpdateInitiativeRequest":
        if not any(getattr(self, field) is not None for field in (
            "title", "objective", "scope", "problem_id", "hypothesis_ids", "objective_ids",
            "evidence_ids", "out_of_scope", "readiness_score", "readiness_confidence",
            "delivery_confidence", "outcome_confidence", "status",
        )):
            raise ValueError("At least one Initiative field must be provided")
        return self