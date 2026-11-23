from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import uuid4


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty text")
    return value.strip()


def _target_value(value: Decimal | int | float | str | None) -> Decimal:
    if value is None:
        raise ValueError("target is required")

    try:
        target = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("target must be numeric") from error

    if not target.is_finite():
        raise ValueError("target must be finite")
    return target


@dataclass(slots=True)
class KeyResult:
    metric: str
    target: Decimal | int | float | str | None
    due_date: date | None
    current_value: Decimal | int | float | str | None = None
    unit: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.metric = _required_text(self.metric, "metric")
        self.target = _target_value(self.target)
        if self.due_date is None:
            raise ValueError("due date is required")
        if not isinstance(self.due_date, date):
            raise ValueError("due date must be a date")
        if self.current_value is not None:
            self.current_value = _target_value(self.current_value)
        if self.unit is not None:
            self.unit = _required_text(self.unit, "unit")


@dataclass(slots=True)
class Objective:
    title: str
    description: str
    key_results: list[KeyResult]
    product_id: str | None = None
    workspace_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.title = _required_text(self.title, "title")
        self.description = _required_text(self.description, "description")
        if not self.key_results:
            raise ValueError("objective must have at least one key result")
        if any(not isinstance(key_result, KeyResult) for key_result in self.key_results):
            raise ValueError("key_results must contain KeyResult entities")
        self.key_results = list(self.key_results)

    def add_key_result(self, key_result: KeyResult) -> None:
        if not isinstance(key_result, KeyResult):
            raise ValueError("key_result must be a KeyResult entity")
        self.key_results.append(key_result)
        self.updated_at = datetime.now(timezone.utc)