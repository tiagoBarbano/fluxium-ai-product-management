from typing import Any

from .models import JobRecord, JobState
from .ports import AsyncJobStore, validate_transition


class JobService:
    def __init__(self, store: AsyncJobStore) -> None:
        self._store = store

    async def submit(
        self,
        name: str,
        payload: dict[str, Any],
        *,
        idempotency_key: str,
        correlation_id: str,
    ) -> JobRecord:
        existing = await self._store.find_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing
        return await self._store.create(
            JobRecord(
                name=name,
                payload=payload,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
            )
        )

    async def transition(
        self,
        job_id: str,
        target: JobState,
        *,
        error: str | None = None,
    ) -> JobRecord:
        job = await self._store.get(job_id)
        if job is None:
            raise KeyError(f"Job not found: {job_id}")
        validate_transition(job.state, target)
        return await self._store.update(job.with_state(target, error=error))

    async def retry(self, job_id: str) -> JobRecord:
        job = await self._store.get(job_id)
        if job is None:
            raise KeyError(f"Job not found: {job_id}")
        validate_transition(job.state, JobState.PENDING)
        return await self._store.update(
            job.with_state(JobState.PENDING, error=None, retry_count=job.retry_count + 1)
        )