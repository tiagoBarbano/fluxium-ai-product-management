import pytest

from app.features.ai_gateway.domain.entities import ProviderGeneration
from app.features.ai_gateway.errors import AIProviderError
from app.features.ai_gateway.fakes import FakeAIProvider
from app.features.ai_gateway.service import AIGatewayService
from app.features.readiness.async_service import ReadinessAssessmentJobService
from app.features.readiness.schemas.async_requests import CreateReadinessAssessmentJobRequest
from app.features.readiness.service import ReadinessAssessmentService
from app.shared.jobs import InMemoryJobStore, JobService, JobState
from app.workers.readiness_worker import run_once

from .test_service import FakeRepository


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


def _job_service(provider: FakeAIProvider, repository: FakeRepository) -> ReadinessAssessmentJobService:
    store = InMemoryJobStore()
    return ReadinessAssessmentJobService(
        JobService(store),
        store,
        ReadinessAssessmentService(repository),
        AIGatewayService(provider),
    )


def _request() -> CreateReadinessAssessmentJobRequest:
    return CreateReadinessAssessmentJobRequest(
        context={
            "initiative": "Improve onboarding",
            "initiative_id": "initiative-1",
            "readiness_dimensions": {
                "problem": "Users abandon onboarding.",
                "audience": "New customers.",
                "value": "Faster activation.",
                "evidence": "Support tickets increased.",
                "solution": "Simplify the first session.",
                "feasibility": "No platform dependency known.",
                "alignment": "Activation objective.",
                "measurement": "Activation rate.",
            },
        },
        context_version="initiative-v3",
        prompt_version="readiness-v1",
        manual_content={"draft": "Keep this content"},
    )


def _generation() -> ProviderGeneration:
    return ProviderGeneration(
        {
            "dimensions": _DIMENSIONS,
            "confidence": 0.8,
        },
        "fake",
        "test-model",
    )


@pytest.mark.asyncio
async def test_submit_is_idempotent_and_worker_creates_assessment_after_ai_success() -> None:
    repository = FakeRepository()
    provider = FakeAIProvider(_generation())
    service = _job_service(provider, repository)

    first = await service.submit(
        "initiative-1", _request(), tenant_id="tenant-1", workspace_ids={"workspace-1"},
        created_by="user-1", idempotency_key="tenant-1:req-1", correlation_id="corr-1",
    )
    second = await service.submit(
        "initiative-1", _request(), tenant_id="tenant-1", workspace_ids={"workspace-1"},
        created_by="user-1", idempotency_key="tenant-1:req-1", correlation_id="corr-2",
    )

    assert second == first
    assert first.state is JobState.PENDING
    assert await run_once(store=service._store, service=service, owner="unit-worker") == 1
    assessment = repository.assessments[0]
    status = await service.get_status(first.job_id)

    assert assessment is not None
    assert assessment.confidence == 0.92
    assert status.state is JobState.SUCCEEDED
    assert status.assessment_id == assessment.id
    assert len(repository.assessments) == 1
    assert provider.commands[0].manual_content == {"draft": "Keep this content"}
    assert provider.commands[0].context["initiative"]["title"] == "Improve onboarding"
    assert provider.commands[0].context["initiative"]["objective"] == "Reduce onboarding friction"
    assert assessment.source_context["submitted_context"] == _request().context
    assert len(assessment.source_context["readiness_dimensions"]) == 8
    assert assessment.source_context["manual_content"] == {"draft": "Keep this content"}

    recreated_service = _job_service(provider, repository)
    recreated_service._store = service._store
    recreated_status = await recreated_service.get_status(first.job_id)
    assert recreated_status.assessment_id == assessment.id


@pytest.mark.asyncio
async def test_provider_failure_marks_job_failed_without_creating_assessment() -> None:
    repository = FakeRepository()
    provider = FakeAIProvider(error=AIProviderError("fake", "provider unavailable", {"draft": "Keep this content"}))
    service = _job_service(provider, repository)
    job = await service.submit(
        "initiative-1", _request(), tenant_id="tenant-1", workspace_ids={"workspace-1"},
        created_by="user-1", idempotency_key="tenant-1:req-2", correlation_id="corr-2",
    )

    assert await run_once(store=service._store, service=service, owner="unit-worker") == 1
    status = await service.get_status(job.job_id)

    assert status.state is JobState.FAILED
    assert status.error == "provider unavailable"
    assert status.assessment_id is None
    assert job.job_id
    assert len(repository.assessments) == 0


@pytest.mark.asyncio
async def test_failed_job_can_retry_and_succeed_without_losing_idempotent_job() -> None:
    repository = FakeRepository()
    provider = FakeAIProvider(error=AIProviderError("fake", "temporary failure"))
    service = _job_service(provider, repository)
    job = await service.submit(
        "initiative-1", _request(), tenant_id="tenant-1", workspace_ids={"workspace-1"},
        created_by="user-1", idempotency_key="tenant-1:req-3", correlation_id="corr-3",
    )

    assert await run_once(store=service._store, service=service, owner="unit-worker") == 1
    provider.error = None
    provider.generation = _generation()
    retried = await service.retry(job.job_id)
    assert await run_once(store=service._store, service=service, owner="unit-worker") == 1
    assessment = repository.assessments[0]
    status = await service.get_status(job.job_id)

    assert retried.job_id == job.job_id
    assert retried.retry_count == 1
    assert assessment is not None
    assert status.state is JobState.SUCCEEDED
    assert len(repository.assessments) == 1
