from dataclasses import dataclass
from datetime import UTC, datetime


class BusinessPlanVersionConflict(ValueError):
    """Raised when a Business Plan write uses a stale version."""


def _text(value: str, field_name: str, max_length: int = 5_000) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} must contain at most {max_length} characters")
    return normalized


def _optional_text(value: str | None, field_name: str, max_length: int = 5_000) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} must contain at most {max_length} characters")
    return normalized or None


def _text_list(values: list[str] | tuple[str, ...], field_name: str) -> tuple[str, ...]:
    return tuple(_text(value, field_name, 1_000) for value in values)


@dataclass(slots=True)
class BusinessPlan:
    id: str
    initiative_id: str
    workspace_id: str
    rationale: str
    what: str | None
    why: str | None
    where: str | None
    when: str | None
    who: str | None
    how: str | None
    how_much: str | None
    metrics: tuple[str, ...]
    risks: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
    version: int = 1

    @classmethod
    def create(
        cls,
        *,
        initiative_id: str,
        workspace_id: str,
        rationale: str,
        what: str | None = None,
        why: str | None = None,
        where: str | None = None,
        when: str | None = None,
        who: str | None = None,
        how: str | None = None,
        how_much: str | None = None,
        metrics: list[str] | tuple[str, ...] = (),
        risks: list[str] | tuple[str, ...] = (),
        plan_id: str | None = None,
        now: datetime | None = None,
    ) -> "BusinessPlan":
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("Business Plan timestamps must be timezone-aware")
        return cls(
            id=_text(plan_id or f"{initiative_id}:business-plan", "id", 200),
            initiative_id=_text(initiative_id, "initiative_id", 100),
            workspace_id=_text(workspace_id, "workspace_id", 100),
            rationale=_text(rationale, "rationale"),
            what=_optional_text(what, "what"),
            why=_optional_text(why, "why"),
            where=_optional_text(where, "where"),
            when=_optional_text(when, "when"),
            who=_optional_text(who, "who"),
            how=_optional_text(how, "how"),
            how_much=_optional_text(how_much, "how_much"),
            metrics=_text_list(metrics, "metrics"),
            risks=_text_list(risks, "risks"),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def update(self, *, expected_version: int, now: datetime | None = None, **changes: object) -> None:
        if expected_version != self.version:
            raise BusinessPlanVersionConflict(
                f"Expected Business Plan version {expected_version}, current version is {self.version}"
            )
        for field_name in ("what", "why", "where", "when", "who", "how", "how_much"):
            value = changes.get(field_name)
            if value is not None:
                setattr(self, field_name, _optional_text(value, field_name))
        if changes.get("rationale") is not None:
            self.rationale = _text(changes["rationale"], "rationale")
        for field_name in ("metrics", "risks"):
            values = changes.get(field_name)
            if values is not None:
                setattr(self, field_name, _text_list(values, field_name))
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("Business Plan timestamps must be timezone-aware")
        self.version += 1
        self.updated_at = timestamp