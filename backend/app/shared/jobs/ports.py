from typing import Protocol

from .models import JobRecord, JobState


class AsyncJobStore(Protocol):
    async def create(self, job: JobRecord) -> JobRecord:
        ...

    async def get(self, job_id: str) -> JobRecord | None:
        ...

    async def update(self, job: JobRecord) -> JobRecord:
        ...

    async def find_by_idempotency_key(self, key: str) -> JobRecord | None:
        ...

    async def find_pending(
        self,
        name: str,
        *,
        tenant_id: str | None = None,
    ) -> list[JobRecord]:
        ...

    async def claim_pending(
        self,
        job_id: str,
        *,
        name: str,
        owner: str,
        tenant_id: str | None = None,
        lease_seconds: int = 300,
    ) -> JobRecord | None:
        ...

    async def release_claim(self, job_id: str, *, owner: str) -> None:
        ...


def validate_transition(current: JobState, target: JobState) -> None:
    allowed = {
        JobState.PENDING: {JobState.RUNNING, JobState.FAILED},
        JobState.RUNNING: {JobState.SUCCEEDED, JobState.FAILED},
        JobState.FAILED: {JobState.PENDING},
        JobState.SUCCEEDED: set(),
    }
    if target not in allowed[current]:
        raise ValueError(f"Invalid job transition: {current} -> {target}")