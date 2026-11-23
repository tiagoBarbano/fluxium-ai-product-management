from pydantic import BaseModel, ConfigDict, Field


class DiscoveryContextRequest(BaseModel):
    affected_audience: str | None = Field(default=None, max_length=2_000)
    observed_problem: str | None = Field(default=None, max_length=2_000)
    occurrence: str | None = Field(default=None, max_length=2_000)
    reported_impact: str | None = Field(default=None, max_length=2_000)
    mentioned_evidence: str | None = Field(default=None, max_length=2_000)
    expected_outcome: str | None = Field(default=None, max_length=2_000)
    measurement: str | None = Field(default=None, max_length=2_000)
    open_questions: str | None = Field(default=None, max_length=2_000)

    model_config = ConfigDict(str_strip_whitespace=True)


class CreateDiscoveryMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10_000)

    model_config = ConfigDict(str_strip_whitespace=True)


class UpdateDiscoveryContextRequest(DiscoveryContextRequest):
    expected_version: int = Field(ge=1)