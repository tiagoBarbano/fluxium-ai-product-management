from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ..domain.entities import ReadinessAssessment


class ReadinessDimensionResponse(BaseModel):
    name: str
    score: float
    justification: str


class ReadinessAssessmentResponse(BaseModel):
    id: str
    initiative_id: str
    workspace_id: str
    score: float
    dimensions: list[ReadinessDimensionResponse]
    missing_information: list[str]
    open_questions: list[str]
    confidence: float
    context_version: str
    provider: str
    model: str
    prompt_version: str
    created_at: datetime
    created_by: str
    source_context: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_entity(cls, assessment: ReadinessAssessment) -> "ReadinessAssessmentResponse":
        return cls(
            id=assessment.id,
            initiative_id=assessment.initiative_id,
            workspace_id=assessment.workspace_id,
            score=assessment.score,
            dimensions=[
                {"name": dimension.name, "score": dimension.score, "justification": dimension.justification}
                for dimension in assessment.dimensions
            ],
            missing_information=list(assessment.missing_information),
            open_questions=list(assessment.open_questions),
            confidence=assessment.confidence,
            context_version=assessment.context_version,
            provider=assessment.provider,
            model=assessment.model,
            prompt_version=assessment.prompt_version,
            created_at=assessment.created_at,
            created_by=assessment.created_by,
            source_context=assessment.source_context,
        )