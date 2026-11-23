from typing import Any

from pydantic import BaseModel, Field


class AIGenerationRequest(BaseModel):
    task: str = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    prompt_version: str = Field(min_length=1)
    context_version: str = Field(min_length=1)
    language: str = Field(default="pt-BR", min_length=2, max_length=20)
    manual_content: Any = None