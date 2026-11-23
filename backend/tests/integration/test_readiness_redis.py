import asyncio
from types import SimpleNamespace

import pytest

from app.features.ai_gateway.domain.entities import ProviderGeneration
from app.features.ai_gateway.errors import AIProviderError
from app.features.ai_gateway.fakes import FakeAIProvider
from app.features.ai_gateway.service import AIGatewayService
from app.features.readiness.async_service import ReadinessAssessmentJobService
from app.features.readiness.schemas.async_requests import CreateReadinessAssessmentJobRequest
from app.features.readiness.service import ReadinessAssessmentService
from app.shared.jobs import JobService, JobState
from app.workers.readiness_worker import run_once


pytestmark = pytest.mark.integration

_DIMENSIONS = [
    {"name": "problem", "score": 100, "justification": "Problem is explicit."},
    {"name": "evidence", "score": 90, "justification": "Evidence is documented."},
    {"name": "hypothesis", "score": 80, "justification": "Hypothesis is testable."},
    {"name": "value", "score": 70, "justification": "Value is described."},
    {"name": "kpi", "score": 60, "justification": "KPI is measurable."},
    {"name": "scope", "score": 50, "justification": "Scope is bounded."},
    {"name": "ux", "score": 40, "justification": "UX is partially defined."},
    {"name": "technical_discovery", "score": 30, "justification": "Technical discovery is partial."},
]


class FakeRepository:
    def __init__(self) -> None:
        self.initiative = SimpleNamespace(id="initiative-redis", workspace_id="workspace-redis")
        self.assessments = []
        self.job_assessment_ids = {}

    async def find_initiative(self, tenant_id: str, initiative_id: str):
        return self.initiative if initiative_id == self.initiative.id else None

    async def insert(self, tenant_id: str, assessment, job_id: str | None = None) -> None:
        self.assessments.append(assessment)
        if job_id is not None:
            self.job_assessment_ids[job_id] = assessment.id

    async def find_id_by_job(self, tenant_id: str, workspace_ids: set[str], job_id: str):
        return self.job_assessment_ids.get(job_id)


def _request() -> CreateReadinessAssessmentJobRequest:
    return CreateReadinessAssessmentJobRequest(
        context={"initiative": "Exercise Redis readiness worker"},
        context_version="initiative-redis-v1",
        prompt_version="readiness-test-v1",
        manual_content={"source": "integration-test"},
    )


def _generation() -> ProviderGeneration:
    return ProviderGeneration({"dimensions": _DIMENSIONS, "confidence": 0.8}, "fake", "test-model")


def _service(redis_job_store, provider: FakeAIProvider, repository: FakeRepository) -> ReadinessAssessmentJobService:
    return ReadinessAssessmentJobService(
        JobService(redis_job_store),
        redis_job_store,
        ReadinessAssessmentService(repository),
        AIGatewayService(provider),
    )


async def _wait_for_terminal(service: ReadinessAssessmentJobService, job_id: str, timeout: float):
    async def poll():
        while True:
            status = await service.get_status(job_id)
            if status.state in (JobState.SUCCEEDED, JobState.FAILED):
                return status
            await asyncio.sleep(0.01)

    return await asyncio.wait_for(poll(), timeout=timeout)


@pytest.mark.asyncio
async def test_redis_submit_worker_succeeds_with_fake_provider(redis_job_store, redis_integration_timeout) -> None:
    repository = FakeRepository()
    service = _service(redis_job_store, FakeAIProvider(_generation()), repository)

    submitted = await service.submit(
        "initiative-redis", _request(), tenant_id="tenant-redis", workspace_ids={"workspace-redis"},
        created_by="integration-test", idempotency_key="tenant-redis:success", correlation_id="correlation-redis-success",
    )
    await run_once(store=redis_job_store, service=service, owner="integration-worker")
    status = await _wait_for_terminal(service, submitted.job_id, redis_integration_timeout)

    assert status.state is JobState.SUCCEEDED
    assert status.assessment_id is not None
    assert len(repository.assessments) == 1


@pytest.mark.asyncio
async def test_redis_submit_worker_marks_failed_without_real_ollama(redis_job_store, redis_integration_timeout) -> None:
    repository = FakeRepository()
    provider = FakeAIProvider(error=AIProviderError("fake", "controlled provider failure"))
    service = _service(redis_job_store, provider, repository)

    submitted = await service.submit(
        "initiative-redis", _request(), tenant_id="tenant-redis", workspace_ids={"workspace-redis"},
        created_by="integration-test", idempotency_key="tenant-redis:failure", correlation_id="correlation-redis-failure",
    )
    await run_once(store=redis_job_store, service=service, owner="integration-worker")
    status = await _wait_for_terminal(service, submitted.job_id, redis_integration_timeout)

    assert status.state is JobState.FAILED
    assert status.error == "controlled provider failure"
    assert status.assessment_id is None
    assert repository.assessments == []