from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..domain.enums import OpportunityStatus


def _normalize_text(value: str) -> str:
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError("must not be blank")
    return normalized_value


class CreateOpportunityRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=5_000)
    objective_ids: list[str] = Field(default_factory=list, max_length=100)

    _validate_product_id = field_validator("product_id")(_normalize_text)
    _validate_title = field_validator("title")(_normalize_text)
    _validate_description = field_validator("description")(_normalize_text)


class UpdateOpportunityRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str | None = Field(default=None, min_length=1)
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=5_000)
    objective_ids: list[str] | None = Field(default=None, max_length=100)
    status: OpportunityStatus | None = None
    expected_version: int = Field(default=1, ge=1)

    _validate_product_id = field_validator("product_id")(_normalize_text)
    _validate_title = field_validator("title")(_normalize_text)
    _validate_description = field_validator("description")(_normalize_text)