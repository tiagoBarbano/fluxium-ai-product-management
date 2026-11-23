from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import ClassVar
from uuid import uuid4

from .enums import ProposalStatus


def _text(value: str, field_name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} must contain at most {max_length} characters")
    return normalized


@dataclass(slots=True)
class Proposal:
    id: str
    initiative_id: str
    assessment_id: str
    changes: dict[str, object]
    status: ProposalStatus
    created_by: str
    decided_by: str | None
    decision_reason: str | None
    created_at: datetime
    decided_at: datetime | None
    expected_initiative_version: int
    business_document: dict[str, object] = field(default_factory=dict)

    MUTABLE_INITIATIVE_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "title", "objective", "scope", "problem_id", "hypothesis_ids",
        "objective_ids", "evidence_ids", "out_of_scope", "readiness_score",
        "readiness_confidence", "delivery_confidence", "outcome_confidence", "status",
    })

    @classmethod
    def create(
        cls,
        *,
        initiative_id: str,
        assessment_id: str,
        changes: dict[str, object],
        created_by: str,
        expected_initiative_version: int,
        business_document: dict[str, object] | None = None,
        proposal_id: str | None = None,
        now: datetime | None = None,
    ) -> "Proposal":
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("Proposal timestamps must be timezone-aware")
        normalized_changes = dict(changes)
        if not normalized_changes:
            raise ValueError("changes must not be empty")
        unsupported = set(normalized_changes) - cls.MUTABLE_INITIATIVE_FIELDS
        if unsupported:
            raise ValueError(f"Unsupported Initiative changes: {sorted(unsupported)}")
        if expected_initiative_version <= 0:
            raise ValueError("expected_initiative_version must be greater than zero")
        return cls(
            id=_text(proposal_id or str(uuid4()), "id", 100),
            initiative_id=_text(initiative_id, "initiative_id", 100),
            assessment_id=_text(assessment_id, "assessment_id", 100),
            changes=normalized_changes,
            status=ProposalStatus.PENDING,
            created_by=_text(created_by, "created_by", 100),
            decided_by=None,
            decision_reason=None,
            created_at=timestamp,
            decided_at=None,
            expected_initiative_version=expected_initiative_version,
            business_document=dict(business_document or {}),
        )

    def decide(self, status: ProposalStatus, decided_by: str, reason: str | None = None, now: datetime | None = None) -> None:
        if self.status is not ProposalStatus.PENDING:
            raise ValueError("Proposal has already been decided")
        if status is ProposalStatus.REJECTED and not reason:
            raise ValueError("A rejection reason is required")
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("Proposal timestamps must be timezone-aware")
        self.status = status
        self.decided_by = _text(decided_by, "decided_by", 100)
        self.decision_reason = reason.strip() if reason else None
        self.decided_at = timestamp