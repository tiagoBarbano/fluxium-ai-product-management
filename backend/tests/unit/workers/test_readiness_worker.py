import asyncio

import pytest

from app.shared.jobs import InMemoryJobStore, JobRecord
from app.workers.readiness_worker import run_once


class FakeReadinessService:
    def __init__(self) -> None:
        self.processed: list[str] = []

    async def run_claimed(self, job_id: str) -> None:
        await asyncio.sleep(0)
        self.processed.append(job_id)


@pytest.mark.asyncio
async def test_run_once_claims_a_job_only_once_when_workers_race() -> None:
    store = InMemoryJobStore()
    job = await store.create(JobRecord(
        name="readiness-assessment",
        payload={"tenant_id": "tenant-1"},
        idempotency_key="worker-race",
        correlation_id="corr-worker",
    ))
    first_service = FakeReadinessService()
    second_service = FakeReadinessService()

    processed = await asyncio.gather(
        run_once(
            store=store,
            service=first_service,  # type: ignore[arg-type]
            owner="worker-a",
        ),
        run_once(
            store=store,
            service=second_service,  # type: ignore[arg-type]
            owner="worker-b",
        ),
    )

    assert processed == [1, 0]
    assert first_service.processed + second_service.processed == [job.id]