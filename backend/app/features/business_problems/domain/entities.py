from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .enums import BusinessProblemStatus


class BusinessProblemVersionConflict(ValueError):
    """Raised when a write is based on a stale Business Problem version."""


def _required_text(value: str, field_name: str, max_length: int) -> str:
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
class BusinessProblem:
    id: str
    workspace_id: str
    product_id: str
    opportunity_id: str
    description: str
    audience: str
    reported_impact: str
    estimated_impact: str | None
    status: BusinessProblemStatus
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
        description: str,
        audience: str,
        reported_impact: str,
        created_by: str,
        estimated_impact: str | None = None,
        problem_id: str | None = None,
        now: datetime | None = None,
    ) -> "BusinessProblem":
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("Business Problem timestamps must be timezone-aware")
        return cls(
            id=_required_text(problem_id or str(uuid4()), "id", 100),
            workspace_id=_required_text(workspace_id, "workspace_id", 100),
            product_id=_required_text(product_id, "product_id", 100),
            opportunity_id=_required_text(opportunity_id, "opportunity_id", 100),
            description=_required_text(description, "description", 5_000),
            audience=_required_text(audience, "audience", 2_000),
            reported_impact=_required_text(reported_impact, "reported_impact", 2_000),
            estimated_impact=_optional_text(estimated_impact, "estimated_impact", 2_000),
            status=BusinessProblemStatus.OPEN,
            created_by=_required_text(created_by, "created_by", 100),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def update(
        self,
        *,
        expected_version: int,
        description: str | None = None,
        audience: str | None = None,
        reported_impact: str | None = None,
        estimated_impact: str | None = None,
        status: BusinessProblemStatus | None = None,
        now: datetime | None = None,
    ) -> None:
        self._check_version(expected_version)
        if description is not None:
            self.description = _required_text(description, "description", 5_000)
        if audience is not None:
            self.audience = _required_text(audience, "audience", 2_000)
        if reported_impact is not None:
            self.reported_impact = _required_text(reported_impact, "reported_impact", 2_000)
        if estimated_impact is not None:
            self.estimated_impact = _optional_text(estimated_impact, "estimated_impact", 2_000)
        if status is not None:
            self.status = BusinessProblemStatus(status)
        self._touch(now)

    def _check_version(self, expected_version: int) -> None:
        if expected_version != self.version:
            raise BusinessProblemVersionConflict(
                f"Expected Business Problem version {expected_version}, current version is {self.version}"
            )

    def _touch(self, now: datetime | None) -> None:
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("Business Problem timestamps must be timezone-aware")
        self.version += 1
        self.updated_at = timestamp