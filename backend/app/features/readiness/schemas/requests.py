from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..domain.entities import DIMENSION_WEIGHTS


class ReadinessDimensionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=50)
    score: float = Field(ge=0, le=100)
    justification: str = Field(min_length=1, max_length=5_000)


class CreateReadinessAssessmentRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    dimensions: list[ReadinessDimensionRequest] = Field(min_length=8, max_length=8)
    missing_information: list[str] = Field(default_factory=list, max_length=100)
    open_questions: list[str] = Field(default_factory=list, max_length=100)
    confidence: float = Field(ge=0, le=1)
    context_version: str = Field(min_length=1, max_length=200)
    provider: str = Field(default="manual", min_length=1, max_length=100)
    model: str = Field(default="deterministic", min_length=1, max_length=200)
    prompt_version: str = Field(default="manual-v1", min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_dimensions(self) -> "CreateReadinessAssessmentRequest":
        names = [dimension.name for dimension in self.dimensions]
        if len(set(names)) != len(names) or set(names) != set(DIMENSION_WEIGHTS):
            raise ValueError("dimensions must contain each Product Readiness dimension exactly once")
        return self