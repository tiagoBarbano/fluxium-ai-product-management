from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .enums import EvidenceOrigin, EvidenceType


def _required_text(value: str, field_name: str, max_length: int = 200) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} must contain at most {max_length} characters")
    return normalized


def _optional_text(value: str | None, field_name: str, max_length: int) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} must contain at most {max_length} characters")
    return normalized or None


@dataclass(slots=True)
class Evidence:
    id: str
    workspace_id: str
    opportunity_id: str
    problem_id: str | None
    hypothesis_id: str | None
    type: EvidenceType
    origin: EvidenceOrigin
    description: str
    source: str | None
    reference: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: str,
        opportunity_id: str,
        evidence_type: EvidenceType,
        origin: EvidenceOrigin,
        description: str,
        created_by: str,
        problem_id: str | None = None,
        hypothesis_id: str | None = None,
        source: str | None = None,
        reference: str | None = None,
        evidence_id: str | None = None,
        now: datetime | None = None,
    ) -> "Evidence":
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("Evidence timestamps must be timezone-aware")
        return cls(
            id=_required_text(evidence_id or str(uuid4()), "id"),
            workspace_id=_required_text(workspace_id, "workspace_id"),
            opportunity_id=_required_text(opportunity_id, "opportunity_id"),
            problem_id=_optional_text(problem_id, "problem_id", 100),
            hypothesis_id=_optional_text(hypothesis_id, "hypothesis_id", 100),
            type=EvidenceType(evidence_type),
            origin=EvidenceOrigin(origin),
            description=_required_text(description, "description", 5_000),
            source=_optional_text(source, "source", 500),
            reference=_optional_text(reference, "reference", 2_000),
            created_by=_required_text(created_by, "created_by", 100),
            created_at=timestamp,
            updated_at=timestamp,
        )