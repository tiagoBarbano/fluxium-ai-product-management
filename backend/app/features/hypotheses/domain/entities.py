from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .enums import HypothesisStatus


def _text(value: str, field_name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} must contain at most {max_length} characters")
    return normalized


def _confidence(value: float) -> float:
    if not 0 <= value <= 1:
        raise ValueError("confidence must be between 0 and 1")
    return value


@dataclass(slots=True)
class Hypothesis:
    id: str
    workspace_id: str
    opportunity_id: str
    statement: str
    expected_behavior: str
    expected_outcome: str
    evidence_ids: list[str]
    confidence: float
    status: HypothesisStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    version: int = 1

    @classmethod
    def create(
        cls,
        *,
        workspace_id: str,
        opportunity_id: str,
        statement: str,
        expected_behavior: str,
        expected_outcome: str,
        evidence_ids: list[str],
        confidence: float,
        created_by: str,
        hypothesis_id: str | None = None,
        now: datetime | None = None,
    ) -> "Hypothesis":
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("Hypothesis timestamps must be timezone-aware")
        return cls(
            id=_text(hypothesis_id or str(uuid4()), "id", 100),
            workspace_id=_text(workspace_id, "workspace_id", 100),
            opportunity_id=_text(opportunity_id, "opportunity_id", 100),
            statement=_text(statement, "statement", 5_000),
            expected_behavior=_text(expected_behavior, "expected_behavior", 5_000),
            expected_outcome=_text(expected_outcome, "expected_outcome", 5_000),
            evidence_ids=list(dict.fromkeys(_text(item, "evidence_id", 100) for item in evidence_ids)),
            confidence=_confidence(confidence),
            status=HypothesisStatus.DRAFT,
            created_by=_text(created_by, "created_by", 100),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def update(self, *, expected_version: int, now: datetime | None = None, **changes: object) -> None:
        if expected_version != self.version:
            raise ValueError(f"Expected Hypothesis version {expected_version}, current version is {self.version}")
        for field_name in ("statement", "expected_behavior", "expected_outcome"):
            value = changes.get(field_name)
            if value is not None:
                setattr(self, field_name, _text(str(value), field_name, 5_000))
        if changes.get("evidence_ids") is not None:
            self.evidence_ids = list(dict.fromkeys(_text(str(item), "evidence_id", 100) for item in changes["evidence_ids"]))
        if changes.get("confidence") is not None:
            self.confidence = _confidence(float(changes["confidence"]))
        if changes.get("status") is not None:
            self.status = HypothesisStatus(changes["status"])
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("Hypothesis timestamps must be timezone-aware")
        self.version += 1
        self.updated_at = timestamp