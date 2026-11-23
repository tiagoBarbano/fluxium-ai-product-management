import asyncio

from .models import JobRecord, JobState


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._idempotency: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._claims: dict[str, str] = {}

    async def create(self, job: JobRecord) -> JobRecord:
        async with self._lock:
            existing_id = self._idempotency.get(job.idempotency_key)
            if existing_id is not None:
                return self._jobs[existing_id]
            self._jobs[job.id] = job
            self._idempotency[job.idempotency_key] = job.id
            return job

    async def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)

    async def update(self, job: JobRecord) -> JobRecord:
        if job.id not in self._jobs:
            raise KeyError(f"Job not found: {job.id}")
        self._jobs[job.id] = job
        return job

    async def find_by_idempotency_key(self, key: str) -> JobRecord | None:
        job_id = self._idempotency.get(key)
        return None if job_id is None else self._jobs[job_id]

    async def find_pending(
        self,
        name: str,
        *,
        tenant_id: str | None = None,
    ) -> list[JobRecord]:
        return [
            job for job in self._jobs.values()
            if job.name == name
            and job.state is JobState.PENDING
            and isinstance(job.payload.get("tenant_id"), str)
            and bool(job.payload["tenant_id"])
            and (tenant_id is None or job.payload["tenant_id"] == tenant_id)
        ]

    async def claim_pending(
        self,
        job_id: str,
        *,
        name: str,
        owner: str,
        tenant_id: str | None = None,
        lease_seconds: int = 300,
    ) -> JobRecord | None:
        del lease_seconds
        async with self._lock:
            job = self._jobs.get(job_id)
            if (
                job is None
                or job.name != name
                or job.state is not JobState.PENDING
                or (tenant_id is not None and job.payload.get("tenant_id") != tenant_id)
                or job_id in self._claims
            ):
                return None
            self._claims[job_id] = owner
            running = job.with_state(JobState.RUNNING)
            self._jobs[job_id] = running
            return running

    async def release_claim(self, job_id: str, *, owner: str) -> None:
        async with self._lock:
            if self._claims.get(job_id) == owner:
                self._claims.pop(job_id, None)