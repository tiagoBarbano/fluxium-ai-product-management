from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class AuditEvent:
    tenant_id: str
    workspace_id: str
    actor: str
    action: str
    resource: str
    resource_id: str
    before_version: int | None = None
    after_version: int | None = None
    assessment: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))