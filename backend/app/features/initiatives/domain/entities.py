from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .enums import InitiativeStatus


def _text(value: str, field_name: str, max_length: int) -> str:
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


def _confidence(value: float | None, field_name: str) -> float | None:
    if value is not None and not 0 <= value <= 1:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _identifiers(values: list[str], field_name: str) -> list[str]:
    return list(dict.fromkeys(_text(value, field_name, 100) for value in values))


@dataclass(slots=True)
class Initiative:
    id: str
    workspace_id: str
    product_id: str
    opportunity_id: str
    problem_id: str | None
    title: str
    objective: str
    hypothesis_ids: list[str]
    objective_ids: list[str]
    evidence_ids: list[str]
    scope: str
    out_of_scope: str | None
    status: InitiativeStatus
    readiness_score: float | None
    readiness_confidence: float | None
    delivery_confidence: float | None
    outcome_confidence: float | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    version: int = 1

    @classmethod
    def create(
        cls,
        *,
        workspace_id: str,
        product_id: str,
        opportunity_id: str,
        title: str,
        objective: str,
        scope: str,
        created_by: str,
        problem_id: str | None = None,
        hypothesis_ids: list[str] | None = None,
        objective_ids: list[str] | None = None,
        evidence_ids: list[str] | None = None,
        out_of_scope: str | None = None,
        readiness_score: float | None = None,
        readiness_confidence: float | None = None,
        delivery_confidence: float | None = None,
        outcome_confidence: float | None = None,
        initiative_id: str | None = None,
        now: datetime | None = None,
    ) -> "Initiative":
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("Initiative timestamps must be timezone-aware")
        return cls(
            id=_text(initiative_id or str(uuid4()), "id", 100),
            workspace_id=_text(workspace_id, "workspace_id", 100),
            product_id=_text(product_id, "product_id", 100),
            opportunity_id=_text(opportunity_id, "opportunity_id", 100),
            problem_id=_optional_text(problem_id, "problem_id", 100),
            title=_text(title, "title", 200),
            objective=_text(objective, "objective", 5_000),
            hypothesis_ids=_identifiers(hypothesis_ids or [], "hypothesis_id"),
            objective_ids=_identifiers(objective_ids or [], "objective_id"),
            evidence_ids=_identifiers(evidence_ids or [], "evidence_id"),
            scope=_text(scope, "scope", 5_000),
            out_of_scope=_optional_text(out_of_scope, "out_of_scope", 5_000),
            status=InitiativeStatus.DRAFT,
            readiness_score=_confidence(readiness_score, "readiness_score"),
            readiness_confidence=_confidence(readiness_confidence, "readiness_confidence"),
            delivery_confidence=_confidence(delivery_confidence, "delivery_confidence"),
            outcome_confidence=_confidence(outcome_confidence, "outcome_confidence"),
            created_by=_text(created_by, "created_by", 100),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def update(self, *, expected_version: int, now: datetime | None = None, **changes: object) -> None:
        if expected_version != self.version:
            raise ValueError(f"Expected Initiative version {expected_version}, current version is {self.version}")
        for field_name, max_length in (("title", 200), ("objective", 5_000), ("scope", 5_000)):
            value = changes.get(field_name)
            if value is not None:
                setattr(self, field_name, _text(str(value), field_name, max_length))
        if changes.get("out_of_scope") is not None:
            self.out_of_scope = _optional_text(str(changes["out_of_scope"]), "out_of_scope", 5_000)
        for field_name in ("readiness_score", "readiness_confidence", "delivery_confidence", "outcome_confidence"):
            if changes.get(field_name) is not None:
                setattr(self, field_name, _confidence(float(changes[field_name]), field_name))
        for field_name in ("hypothesis_ids", "objective_ids", "evidence_ids"):
            if changes.get(field_name) is not None:
                setattr(self, field_name, _identifiers(list(changes[field_name]), field_name[:-1]))
        if changes.get("problem_id") is not None:
            self.problem_id = _optional_text(str(changes["problem_id"]), "problem_id", 100)
        if changes.get("status") is not None:
            self.status = InitiativeStatus(changes["status"])
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("Initiative timestamps must be timezone-aware")
        self.version += 1
        self.updated_at = timestamp