from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("must not be blank")
    return normalized


class UpdateBusinessPlanRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    expected_version: int = Field(ge=0)
    rationale: str | None = Field(default=None, min_length=1, max_length=5_000)
    what: str | None = Field(default=None, min_length=1, max_length=5_000)
    why: str | None = Field(default=None, min_length=1, max_length=5_000)
    where: str | None = Field(default=None, min_length=1, max_length=5_000)
    when: str | None = Field(default=None, min_length=1, max_length=5_000)
    who: str | None = Field(default=None, min_length=1, max_length=5_000)
    how: str | None = Field(default=None, min_length=1, max_length=5_000)
    how_much: str | None = Field(default=None, min_length=1, max_length=5_000)
    metrics: list[str] | None = Field(default=None, max_length=20)
    risks: list[str] | None = Field(default=None, max_length=20)

    _validate_texts = field_validator(
        "rationale", "what", "why", "where", "when", "who", "how", "how_much", mode="before"
    )(_normalize)
    _validate_lists = field_validator("metrics", "risks")(
        lambda values: [_normalize(value) for value in values] if values is not None else None
    )