from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from .enums import DiscoveryMessageRole, DiscoverySessionStatus


def _required_text(value: str, field_name: str, max_length: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must not be blank")
    normalized = value.strip()
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} must be at most {max_length} characters")
    return normalized


@dataclass(slots=True)
class DiscoveryContext:
    affected_audience: str | None = None
    observed_problem: str | None = None
    occurrence: str | None = None
    reported_impact: str | None = None
    mentioned_evidence: str | None = None
    expected_outcome: str | None = None
    measurement: str | None = None
    open_questions: str | None = None

    def __post_init__(self) -> None:
        field_names = (
            "affected_audience",
            "observed_problem",
            "occurrence",
            "reported_impact",
            "mentioned_evidence",
            "expected_outcome",
            "measurement",
            "open_questions",
        )
        for field_name in field_names:
            value = getattr(self, field_name)
            if value is not None:
                setattr(self, field_name, _required_text(value, field_name, 2_000))


@dataclass(slots=True)
class DiscoveryMessage:
    session_id: str
    content: str
    sequence: int
    role: DiscoveryMessageRole = DiscoveryMessageRole.USER
    created_by: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.session_id = _required_text(self.session_id, "session_id", 100)
        self.content = _required_text(self.content, "content", 10_000)
        if self.sequence < 1:
            raise ValueError("sequence must be positive")
        self.role = DiscoveryMessageRole(self.role)


@dataclass(slots=True)
class DiscoverySession:
    opportunity_id: str
    workspace_id: str
    created_by: str
    context: DiscoveryContext = field(default_factory=DiscoveryContext)
    status: DiscoverySessionStatus = DiscoverySessionStatus.ACTIVE
    mode: str = "MANUAL"
    version: int = 1
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.opportunity_id = _required_text(self.opportunity_id, "opportunity_id", 100)
        self.workspace_id = _required_text(self.workspace_id, "workspace_id", 100)
        self.created_by = _required_text(self.created_by, "created_by", 200)
        self.status = DiscoverySessionStatus(self.status)
        if self.mode != "MANUAL":
            raise ValueError("only MANUAL discovery is currently supported")

    def transition_to(self, target: DiscoverySessionStatus) -> None:
        target = DiscoverySessionStatus(target)
        allowed = {
            DiscoverySessionStatus.ACTIVE: {
                DiscoverySessionStatus.PAUSED,
                DiscoverySessionStatus.COMPLETED,
                DiscoverySessionStatus.FAILED,
            },
            DiscoverySessionStatus.PAUSED: {DiscoverySessionStatus.ACTIVE},
            DiscoverySessionStatus.COMPLETED: set(),
            DiscoverySessionStatus.FAILED: set(),
        }
        if target not in allowed[self.status]:
            raise ValueError(f"Invalid discovery session transition: {self.status} -> {target}")
        self.status = target
        self.updated_at = datetime.now(UTC)

    def update_context(self, context: DiscoveryContext, expected_version: int) -> None:
        if self.version != expected_version:
            raise ValueError("Discovery session was modified by another request")
        if self.status is DiscoverySessionStatus.COMPLETED:
            raise ValueError("Completed discovery sessions cannot be updated")
        self.context = context
        self.version += 1
        self.updated_at = datetime.now(UTC)