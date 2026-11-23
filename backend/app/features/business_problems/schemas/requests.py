from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..domain.enums import BusinessProblemStatus


def _normalize_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("must not be blank")
    return normalized


class CreateBusinessProblemRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    description: str = Field(min_length=1, max_length=5_000)
    audience: str = Field(min_length=1, max_length=2_000)
    reported_impact: str = Field(min_length=1, max_length=2_000)
    estimated_impact: str | None = Field(default=None, max_length=2_000)

    _validate_description = field_validator("description")(_normalize_text)
    _validate_audience = field_validator("audience")(_normalize_text)
    _validate_reported_impact = field_validator("reported_impact")(_normalize_text)
    _validate_estimated_impact = field_validator("estimated_impact")(_normalize_text)


class UpdateBusinessProblemRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    expected_version: int = Field(ge=1)
    description: str | None = Field(default=None, min_length=1, max_length=5_000)
    audience: str | None = Field(default=None, min_length=1, max_length=2_000)
    reported_impact: str | None = Field(default=None, min_length=1, max_length=2_000)
    estimated_impact: str | None = Field(default=None, max_length=2_000)
    status: BusinessProblemStatus | None = None

    _validate_description = field_validator("description")(_normalize_text)
    _validate_audience = field_validator("audience")(_normalize_text)
    _validate_reported_impact = field_validator("reported_impact")(_normalize_text)
    _validate_estimated_impact = field_validator("estimated_impact")(_normalize_text)