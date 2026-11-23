from typing import Any

from pydantic import BaseModel, Field


class AIGenerationResponse(BaseModel):
    result: Any
    confidence: float = Field(ge=0.0, le=1.0)
    missing_information: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    provider: str
    model: str
    prompt_version: str
    context_version: str