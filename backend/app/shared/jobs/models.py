from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class JobState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class JobRecord:
    name: str
    payload: dict[str, Any]
    idempotency_key: str
    correlation_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    state: JobState = JobState.PENDING
    retry_count: int = 0
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_state(
        self,
        state: JobState,
        *,
        error: str | None = None,
        retry_count: int | None = None,
    ) -> "JobRecord":
        return JobRecord(
            id=self.id,
            name=self.name,
            payload=self.payload,
            idempotency_key=self.idempotency_key,
            correlation_id=self.correlation_id,
            state=state,
            retry_count=self.retry_count if retry_count is None else retry_count,
            error=error,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )