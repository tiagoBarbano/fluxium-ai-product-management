from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar, Iterable
from uuid import uuid4


DIMENSION_WEIGHTS: dict[str, float] = {
    "problem": 0.15,
    "evidence": 0.15,
    "hypothesis": 0.10,
    "value": 0.15,
    "kpi": 0.10,
    "scope": 0.15,
    "ux": 0.10,
    "technical_discovery": 0.10,
}


def calculate_readiness_confidence(
    *,
    dimensions: Iterable["ReadinessDimensionScore"],
    missing_information: Iterable[str],
    open_questions: Iterable[str],
    provider_confidence: float,
    context_sections: Iterable[Any],
) -> float:
    """Calculate confidence in the assessment evidence, not in its score."""
    if not 0 <= provider_confidence <= 1:
        raise ValueError("provider_confidence must be between 0 and 1")

    dimension_list = tuple(dimensions)
    covered_dimensions = {
        dimension.name
        for dimension in dimension_list
        if dimension.name in DIMENSION_WEIGHTS and dimension.justification.strip()
    }
    dimension_completeness = len(covered_dimensions) / len(DIMENSION_WEIGHTS)
    context_completeness = sum(_has_content(section) for section in context_sections) / 3
    missing_penalty = min(0.4, 0.05 * len(tuple(missing_information)))
    question_penalty = min(0.2, 0.05 * len(tuple(open_questions)))
    confidence = (
        (0.4 * provider_confidence)
        + (0.3 * context_completeness)
        + (0.3 * dimension_completeness)
        - missing_penalty
        - question_penalty
    )
    return round(max(0.0, min(1.0, confidence)), 4)


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict | list | tuple | set):
        return bool(value)
    return True


def _text(value: str, field_name: str, max_length: int = 5_000) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} must contain at most {max_length} characters")
    return normalized


def _text_list(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    return tuple(_text(value, field_name) for value in values)


@dataclass(frozen=True, slots=True)
class ReadinessDimensionScore:
    name: str
    score: float
    justification: str

    def __post_init__(self) -> None:
        if self.name not in DIMENSION_WEIGHTS:
            raise ValueError(f"Unknown readiness dimension: {self.name}")
        if not 0 <= self.score <= 100:
            raise ValueError("Dimension scores must be between 0 and 100")
        _text(self.justification, "justification")


@dataclass(frozen=True, slots=True)
class ReadinessAssessment:
    id: str
    initiative_id: str
    workspace_id: str
    score: float
    dimensions: tuple[ReadinessDimensionScore, ...]
    missing_information: tuple[str, ...]
    open_questions: tuple[str, ...]
    confidence: float
    context_version: str
    provider: str
    model: str
    prompt_version: str
    created_at: datetime
    created_by: str
    source_context: dict[str, Any]

    DIMENSION_WEIGHTS: ClassVar[dict[str, float]] = DIMENSION_WEIGHTS

    @classmethod
    def create(
        cls,
        *,
        initiative_id: str,
        workspace_id: str,
        dimensions: tuple[ReadinessDimensionScore, ...],
        missing_information: tuple[str, ...],
        open_questions: tuple[str, ...],
        confidence: float,
        context_version: str,
        provider: str,
        model: str,
        prompt_version: str,
        created_by: str,
        source_context: dict[str, Any] | None = None,
        assessment_id: str | None = None,
        now: datetime | None = None,
    ) -> "ReadinessAssessment":
        expected = set(DIMENSION_WEIGHTS)
        actual = {dimension.name for dimension in dimensions}
        if actual != expected or len(dimensions) != len(expected):
            raise ValueError("All readiness dimensions must be provided exactly once")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("Assessment timestamps must be timezone-aware")
        score = round(sum(dimension.score * DIMENSION_WEIGHTS[dimension.name] for dimension in dimensions), 2)
        return cls(
            id=_text(assessment_id or str(uuid4()), "id", 100),
            initiative_id=_text(initiative_id, "initiative_id", 100),
            workspace_id=_text(workspace_id, "workspace_id", 100),
            score=score,
            dimensions=tuple(dimensions),
            missing_information=_text_list(missing_information, "missing_information"),
            open_questions=_text_list(open_questions, "open_questions"),
            confidence=confidence,
            context_version=_text(context_version, "context_version", 200),
            provider=_text(provider, "provider", 100),
            model=_text(model, "model", 200),
            prompt_version=_text(prompt_version, "prompt_version", 100),
            created_at=timestamp,
            created_by=_text(created_by, "created_by", 100),
            source_context=dict(source_context or {}),
        )