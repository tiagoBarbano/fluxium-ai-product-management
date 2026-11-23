from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import AuditEvent


MAX_AUDIT_PAGE_SIZE = 100


class AuditEventQuery(BaseModel):
    limit: int = Field(default=20, ge=1, le=MAX_AUDIT_PAGE_SIZE)
    cursor: str | None = None
    resource: str | None = Field(default=None, min_length=1, max_length=100)
    resource_id: str | None = Field(default=None, min_length=1, max_length=100)
    initiative_id: str | None = Field(default=None, min_length=1, max_length=100)


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    tenant_id: str
    workspace_id: str
    actor: str
    action: str
    resource: str
    resource_id: str
    before_version: int | None
    after_version: int | None
    assessment: str | None
    provider: str | None
    model: str | None
    prompt: str | None
    correlation_id: str | None
    trace_id: str | None
    metadata: dict[str, object]
    created_at: datetime

    @classmethod
    def from_event(cls, event: AuditEvent) -> "AuditEventResponse":
        return cls.model_validate(event, from_attributes=True)


class AuditEventPage(BaseModel):
    items: list[AuditEventResponse]
    next_cursor: str | None = None