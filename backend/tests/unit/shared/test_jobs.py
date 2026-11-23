import asyncio

import pytest

from app.config.settings import Settings
from app.shared.jobs import InMemoryJobStore, JobService, JobState
from app.shared.jobs.models import JobRecord
from app.shared.jobs.redis import RedisJobStore


class FakeRedis:
    def __init__(self) -> None:
        self.values = {}

    async def set(self, key, value, nx=False, ex=None):
        del ex
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    async def get(self, key):
        return self.values.get(key)

    async def scan_iter(self, match):
        prefix = match.removesuffix("*")
        for key in list(self.values):
            if key.startswith(prefix):
                yield key

    async def eval(self, _script, _numkeys, key, token):
        if self.values.get(key) == token:
            del self.values[key]
            return 1
        return 0


@pytest.mark.asyncio
async def test_submit_is_idempotent_and_preserves_correlation() -> None:
    service = JobService(InMemoryJobStore())

    first = await service.submit(
        "assessment",
        {"product_id": "product-1"},
        idempotency_key="request-1",
        correlation_id="corr-1",
    )
    second = await service.submit(
        "assessment",
        {"different": True},
        idempotency_key="request-1",
        correlation_id="corr-2",
    )

    assert second == first
    assert first.state is JobState.PENDING
    assert first.correlation_id == "corr-1"


@pytest.mark.asyncio
async def test_job_transitions_and_retry_increment_count() -> None:
    service = JobService(InMemoryJobStore())
    job = await service.submit("assessment", {}, idempotency_key="request-2", correlation_id="corr")

    running = await service.transition(job.id, JobState.RUNNING)
    failed = await service.transition(running.id, JobState.FAILED, error="provider timeout")
    retried = await service.retry(failed.id)

    assert failed.error == "provider timeout"
    assert retried.state is JobState.PENDING
    assert retried.retry_count == 1
    assert retried.error is None


@pytest.mark.asyncio
async def test_succeeded_job_cannot_transition_again() -> None:
    service = JobService(InMemoryJobStore())
    job = await service.submit("assessment", {}, idempotency_key="request-3", correlation_id="corr")
    await service.transition(job.id, JobState.RUNNING)
    succeeded = await service.transition(job.id, JobState.SUCCEEDED)

    with pytest.raises(ValueError, match="Invalid job transition"):
        await service.transition(succeeded.id, JobState.RUNNING)


@pytest.mark.asyncio
async def test_redis_store_round_trips_job_without_network() -> None:
    store = RedisJobStore(FakeRedis())
    job = JobRecord(
        name="assessment",
        payload={"product_id": "product-1"},
        idempotency_key="request-redis",
        correlation_id="corr-redis",
    )

    created = await store.create(job)
    loaded = await store.get(job.id)

    assert created == job
    assert loaded == job


@pytest.mark.asyncio
async def test_redis_store_discovers_only_pending_jobs_for_requested_tenant() -> None:
    store = RedisJobStore(FakeRedis())
    await store.create(JobRecord(
        name="readiness-assessment",
        payload={"tenant_id": "tenant-1"},
        idempotency_key="readiness-1",
        correlation_id="corr-1",
    ))
    await store.create(JobRecord(
        name="readiness-assessment",
        payload={"tenant_id": "tenant-2"},
        idempotency_key="readiness-2",
        correlation_id="corr-2",
    ))

    jobs = await store.find_pending("readiness-assessment", tenant_id="tenant-1")

    assert len(jobs) == 1
    assert jobs[0].payload["tenant_id"] == "tenant-1"


@pytest.mark.asyncio
async def test_redis_claim_allows_only_one_concurrent_worker() -> None:
    store = RedisJobStore(FakeRedis())
    job = await store.create(JobRecord(
        name="readiness-assessment",
        payload={"tenant_id": "tenant-1"},
        idempotency_key="readiness-claim",
        correlation_id="corr-claim",
    ))

    claims = await asyncio.gather(
        store.claim_pending(job.id, name="readiness-assessment", owner="worker-a"),
        store.claim_pending(job.id, name="readiness-assessment", owner="worker-b"),
    )

    assert sum(claim is not None for claim in claims) == 1
    assert (await store.get(job.id)).state is JobState.RUNNING


def test_redis_store_uses_configured_redis_url(monkeypatch) -> None:
    captured = {}

    def fake_from_url(url, decode_responses):
        captured.update(url=url, decode_responses=decode_responses)
        return FakeRedis()

    monkeypatch.setattr("app.shared.jobs.redis.Redis.from_url", fake_from_url)
    RedisJobStore.from_settings(Settings(redis_url="redis://example:6379/4"))

    assert captured == {"url": "redis://example:6379/4", "decode_responses": True}