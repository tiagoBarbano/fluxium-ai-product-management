import json
from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import uuid4

from redis.asyncio import Redis

from ...config.settings import Settings, get_settings
from .models import JobRecord, JobState


class RedisJobStore:
    def __init__(self, client: Redis, *, key_prefix: str = "fluxium:job") -> None:
        self._client = client
        self._key_prefix = key_prefix

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "RedisJobStore":
        resolved = settings or get_settings()
        return cls(Redis.from_url(resolved.redis_url, decode_responses=True))

    async def close(self) -> None:
        await self._client.aclose()

    def _job_key(self, job_id: str) -> str:
        return f"{self._key_prefix}:{job_id}"

    def _idempotency_key(self, key: str) -> str:
        return f"{self._key_prefix}:idempotency:{key}"

    def _claim_key(self, job_id: str) -> str:
        return f"{self._key_prefix}:claim:{job_id}"

    @staticmethod
    def _serialize(job: JobRecord) -> str:
        document = asdict(job)
        document["state"] = job.state.value
        document["created_at"] = job.created_at.isoformat()
        document["updated_at"] = job.updated_at.isoformat()
        return json.dumps(document)

    @staticmethod
    def _deserialize(raw: str) -> JobRecord:
        document: dict[str, Any] = json.loads(raw)
        document["state"] = JobState(document["state"])
        document["created_at"] = datetime.fromisoformat(document["created_at"])
        document["updated_at"] = datetime.fromisoformat(document["updated_at"])
        return JobRecord(**document)

    async def create(self, job: JobRecord) -> JobRecord:
        claimed = await self._client.set(
            self._idempotency_key(job.idempotency_key), job.id, nx=True
        )
        if not claimed:
            existing = await self.find_by_idempotency_key(job.idempotency_key)
            if existing is None:
                raise RuntimeError("Idempotency claim exists without a job")
            return existing
        await self._client.set(self._job_key(job.id), self._serialize(job))
        return job

    async def get(self, job_id: str) -> JobRecord | None:
        raw = await self._client.get(self._job_key(job_id))
        return None if raw is None else self._deserialize(raw)

    async def update(self, job: JobRecord) -> JobRecord:
        if await self._client.get(self._job_key(job.id)) is None:
            raise KeyError(f"Job not found: {job.id}")
        await self._client.set(self._job_key(job.id), self._serialize(job))
        return job

    async def find_by_idempotency_key(self, key: str) -> JobRecord | None:
        job_id = await self._client.get(self._idempotency_key(key))
        return None if job_id is None else await self.get(job_id)

    async def find_pending(
        self,
        name: str,
        *,
        tenant_id: str | None = None,
    ) -> list[JobRecord]:
        jobs: list[JobRecord] = []
        async for key in self._client.scan_iter(match=f"{self._key_prefix}:*"):
            if ":idempotency:" in key or ":claim:" in key:
                continue
            raw = await self._client.get(key)
            if raw is None:
                continue
            job = self._deserialize(raw)
            if (
                job.name == name
                and job.state is JobState.PENDING
                and isinstance(job.payload.get("tenant_id"), str)
                and bool(job.payload["tenant_id"])
                and (tenant_id is None or job.payload["tenant_id"] == tenant_id)
            ):
                jobs.append(job)
        return jobs

    async def claim_pending(
        self,
        job_id: str,
        *,
        name: str,
        owner: str,
        tenant_id: str | None = None,
        lease_seconds: int = 300,
    ) -> JobRecord | None:
        token = f"{owner}:{uuid4()}"
        claimed = await self._client.set(
            self._claim_key(job_id), token, nx=True, ex=lease_seconds
        )
        if not claimed:
            return None
        job = await self.get(job_id)
        if (
            job is None
            or job.name != name
            or job.state is not JobState.PENDING
            or (tenant_id is not None and job.payload.get("tenant_id") != tenant_id)
        ):
            await self._release_token(job_id, token)
            return None
        running = job.with_state(JobState.RUNNING)
        await self.update(running)
        return running

    async def release_claim(self, job_id: str, *, owner: str) -> None:
        token = await self._client.get(self._claim_key(job_id))
        if token is not None and token.startswith(f"{owner}:"):
            await self._release_token(job_id, token)

    async def _release_token(self, job_id: str, token: str) -> None:
        await self._client.eval(
            "if redis.call('get', KEYS[1]) == ARGV[1] then "
            "return redis.call('del', KEYS[1]) else return 0 end",
            1,
            self._claim_key(job_id),
            token,
        )