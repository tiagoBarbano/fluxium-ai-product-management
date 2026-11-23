from typing import Any, Literal

from pydantic import BaseModel, Field


class CreateReadinessAssessmentJobRequest(BaseModel):
    context: dict[str, Any] = Field(default_factory=dict)
    context_version: str = Field(min_length=1, max_length=200)
    prompt_version: str = Field(min_length=1, max_length=100)
    language: Literal["pt-BR", "en-US"] = "pt-BR"
    manual_content: Any = None