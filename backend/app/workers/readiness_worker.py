import argparse
import asyncio
import os
from uuid import uuid4

from ..database.mongo import get_database
from ..features.ai_gateway.providers.ollama import OllamaProvider
from ..features.ai_gateway.service import AIGatewayService
from ..features.readiness.async_service import ReadinessAssessmentJobService
from ..features.readiness.repository import MongoReadinessAssessmentRepository
from ..features.readiness.service import ReadinessAssessmentService
from ..shared.jobs import AsyncJobStore, JobService, RedisJobStore


READINESS_JOB_NAME = "readiness-assessment"


async def process_readiness_job(
    job_id: str,
    *,
    store: AsyncJobStore,
    service: ReadinessAssessmentJobService,
    owner: str,
    tenant_id: str | None = None,
    lease_seconds: int = 300,
) -> bool:
    """Claim and process one readiness job, returning whether it was claimed."""
    claimed = await store.claim_pending(
        job_id,
        name=READINESS_JOB_NAME,
        owner=owner,
        tenant_id=tenant_id,
        lease_seconds=lease_seconds,
    )
    if claimed is None:
        return False
    try:
        await service.run_claimed(job_id)
        return True
    finally:
        await store.release_claim(job_id, owner=owner)


async def run_once(
    *,
    store: AsyncJobStore,
    service: ReadinessAssessmentJobService,
    owner: str | None = None,
    tenant_id: str | None = None,
    lease_seconds: int = 300,
) -> int:
    """Claim and process all currently visible pending jobs once."""
    worker_id = owner or str(uuid4())
    pending = await store.find_pending(READINESS_JOB_NAME, tenant_id=tenant_id)
    processed = 0
    for job in pending:
        if await process_readiness_job(
            job.id,
            store=store,
            service=service,
            owner=worker_id,
            tenant_id=tenant_id,
            lease_seconds=lease_seconds,
        ):
            processed += 1
    return processed


async def run_forever(
    *,
    store: AsyncJobStore,
    service: ReadinessAssessmentJobService,
    poll_interval: float = 1.0,
    tenant_id: str | None = None,
    lease_seconds: int = 300,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Poll Redis until cancelled or an optional stop event is set."""
    if poll_interval <= 0:
        raise ValueError("poll_interval must be greater than zero")
    if lease_seconds <= 0:
        raise ValueError("lease_seconds must be greater than zero")
    worker_id = str(uuid4())
    shutdown = stop_event or asyncio.Event()
    while not shutdown.is_set():
        await run_once(
            store=store,
            service=service,
            owner=worker_id,
            tenant_id=tenant_id,
            lease_seconds=lease_seconds,
        )
        try:
            await asyncio.wait_for(shutdown.wait(), timeout=poll_interval)
        except TimeoutError:
            continue


def build_service(store: AsyncJobStore) -> ReadinessAssessmentJobService:
    """Build production dependencies; callers and tests may inject their own service."""
    database = get_database()
    return ReadinessAssessmentJobService(
        JobService(store),
        store,
        ReadinessAssessmentService(
            MongoReadinessAssessmentRepository(database["assessments"], database["initiatives"])
        ),
        AIGatewayService(OllamaProvider()),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process readiness assessment jobs from Redis")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=float(os.getenv("FLUXIUM_READINESS_WORKER_POLL_INTERVAL", "1")),
    )
    parser.add_argument(
        "--lease-seconds",
        type=int,
        default=int(os.getenv("FLUXIUM_READINESS_WORKER_LEASE_SECONDS", "300")),
    )
    parser.add_argument("--tenant-id", default=os.getenv("FLUXIUM_READINESS_WORKER_TENANT_ID"))
    return parser


async def _main(args: argparse.Namespace) -> None:
    store = RedisJobStore.from_settings()
    service = build_service(store)
    try:
        await run_forever(
            store=store,
            service=service,
            poll_interval=args.poll_interval,
            tenant_id=args.tenant_id,
            lease_seconds=args.lease_seconds,
        )
    finally:
        await store.close()


def main() -> None:
    asyncio.run(_main(_parser().parse_args()))


if __name__ == "__main__":
    main()