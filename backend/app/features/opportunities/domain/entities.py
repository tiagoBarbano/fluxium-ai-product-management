from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import ClassVar

from .enums import OpportunityStatus


@dataclass
class Opportunity:
    id: str
    product_id: str
    title: str
    description: str
    objective_ids: list[str] = field(default_factory=list)
    status: OpportunityStatus = OpportunityStatus.NEW
    workspace_id: str | None = None
    created_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 1

    def __post_init__(self) -> None:
        self.id = self._validate_text(self.id, "id")
        self.product_id = self._validate_text(self.product_id, "product_id")
        self.title = self._validate_text(self.title, "title", max_length=120)
        self.description = self._validate_text(
            self.description,
            "description",
            max_length=5_000,
        )
        self.objective_ids = list(dict.fromkeys(self.objective_ids))
        self.status = OpportunityStatus(self.status)
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("Opportunity timestamps must be timezone-aware")

    def touch(self) -> None:
        self.version += 1
        self.updated_at = datetime.now(UTC)

    def transition_to(self, target_status: OpportunityStatus) -> None:
        target_status = OpportunityStatus(target_status)
        if target_status not in self._allowed_transitions[self.status]:
            raise ValueError(
                f"Invalid opportunity transition: "
                f"{self.status} -> {target_status}"
            )
        self.status = target_status

    def can_transition_to(self, target_status: OpportunityStatus) -> bool:
        return OpportunityStatus(target_status) in self._allowed_transitions[self.status]

    @staticmethod
    def _validate_text(
        value: str,
        field_name: str,
        *,
        max_length: int | None = None,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError(f"{field_name} must not be blank")
        if max_length is not None and len(normalized_value) > max_length:
            raise ValueError(f"{field_name} must be at most {max_length} characters")
        return normalized_value

    _allowed_transitions: ClassVar[dict[OpportunityStatus, frozenset[OpportunityStatus]]] = {
        OpportunityStatus.NEW: frozenset({OpportunityStatus.DISCOVERY}),
        OpportunityStatus.DISCOVERY: frozenset(
            {OpportunityStatus.QUALIFIED, OpportunityStatus.REJECTED}
        ),
        OpportunityStatus.QUALIFIED: frozenset({OpportunityStatus.CONVERTED}),
        OpportunityStatus.REJECTED: frozenset(),
        OpportunityStatus.CONVERTED: frozenset(),
    }