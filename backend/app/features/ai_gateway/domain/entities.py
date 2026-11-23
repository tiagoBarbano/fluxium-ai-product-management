from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AIGenerationCommand:
    task: str
    context: dict[str, Any]
    output_schema: dict[str, Any]
    prompt_version: str
    context_version: str
    language: str = "pt-BR"
    manual_content: Any = None


@dataclass(frozen=True, slots=True)
class ProviderGeneration:
    result: Any
    provider: str
    model: str


@dataclass(frozen=True, slots=True)
class AIGenerationResult:
    result: Any
    confidence: float
    missing_information: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    provider: str = ""
    model: str = ""
    prompt_version: str = ""
    context_version: str = ""