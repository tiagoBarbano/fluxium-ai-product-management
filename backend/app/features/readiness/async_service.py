from ..ai_gateway.schemas.requests import AIGenerationRequest
from ..ai_gateway.service import AIGatewayService
from ...shared.jobs import AsyncJobStore, JobService, JobState
from .domain.entities import ReadinessAssessment, ReadinessDimensionScore, calculate_readiness_confidence
from .schemas.async_requests import CreateReadinessAssessmentJobRequest
from .schemas.async_responses import ReadinessAssessmentJobResponse
from .schemas.requests import CreateReadinessAssessmentRequest
from .service import ReadinessAssessmentService


class ReadinessAssessmentJobService:
    def __init__(
        self,
        jobs: JobService,
        store: AsyncJobStore,
        assessments: ReadinessAssessmentService,
        ai_gateway: AIGatewayService,
    ) -> None:
        self._jobs = jobs
        self._store = store
        self._assessments = assessments
        self._ai_gateway = ai_gateway

    async def submit(
        self,
        initiative_id: str,
        request: CreateReadinessAssessmentJobRequest,
        *,
        tenant_id: str,
        workspace_ids: set[str] | frozenset[str],
        created_by: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> ReadinessAssessmentJobResponse:
        job = await self._jobs.submit(
            "readiness-assessment",
            {
                "initiative_id": initiative_id,
                "context": request.context,
                "context_version": request.context_version,
                "prompt_version": request.prompt_version,
                "language": request.language,
                "manual_content": request.manual_content,
                "tenant_id": tenant_id,
                "workspace_ids": list(workspace_ids),
                "created_by": created_by,
            },
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        assessment_id = await self._assessment_id_for_job(job)
        return ReadinessAssessmentJobResponse.from_job(job, assessment_id)

    async def run_claimed(self, job_id: str) -> ReadinessAssessment | None:
        job = await self._store.get(job_id)
        if job is None:
            raise KeyError(f"Job not found: {job_id}")
        if job.state is not JobState.RUNNING:
            return None
        return await self._run_claimed(job_id)

    async def _run_claimed(self, job_id: str) -> ReadinessAssessment | None:
        job = await self._store.get(job_id)
        if job is None:
            raise KeyError(f"Job not found: {job_id}")
        try:
            payload = job.payload
            initiative_context = await self._assessments.get_initiative_context(
                payload["initiative_id"], payload["tenant_id"], frozenset(payload["workspace_ids"])
            )
            ai_response = await self._ai_gateway.generate(
                AIGenerationRequest(
                    task="Assess Product Readiness",
                    context={"initiative": initiative_context, "submitted_context": payload["context"]},
                    output_schema={
                        "type": "object",
                        "required": ["dimensions", "missing_information", "open_questions", "confidence"],
                        "properties": {
                            "dimensions": {
                                "type": "array",
                                "minItems": 8,
                                "maxItems": 8,
                                "items": {
                                    "type": "object",
                                    "required": ["name", "score", "justification"],
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "enum": [
                                                "problem",
                                                "evidence",
                                                "hypothesis",
                                                "value",
                                                "kpi",
                                                "scope",
                                                "ux",
                                                "technical_discovery",
                                            ],
                                        },
                                        "score": {"type": "number", "minimum": 0, "maximum": 100},
                                        "justification": {"type": "string"},
                                    },
                                },
                            },
                            "missing_information": {"type": "array", "items": {"type": "string"}},
                            "open_questions": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                    },
                    prompt_version=payload["prompt_version"],
                    context_version=payload["context_version"],
                    language=payload.get("language", "pt-BR"),
                    manual_content=payload["manual_content"],
                )
            )
            if not isinstance(ai_response.result, dict):
                raise ValueError("AI readiness result must be an object")
            assessment_request = CreateReadinessAssessmentRequest.model_validate(
                {
                    **ai_response.result,
                    "provider": ai_response.provider,
                    "model": ai_response.model,
                    "prompt_version": ai_response.prompt_version,
                    "context_version": ai_response.context_version,
                    "missing_information": ai_response.missing_information,
                    "open_questions": ai_response.open_questions,
                    "confidence": ai_response.confidence,
                }
            )
            assessment_request = assessment_request.model_copy(
                update={
                    "confidence": calculate_readiness_confidence(
                        dimensions=tuple(
                            ReadinessDimensionScore(
                                name=dimension.name,
                                score=dimension.score,
                                justification=dimension.justification,
                            )
                            for dimension in assessment_request.dimensions
                        ),
                        missing_information=assessment_request.missing_information,
                        open_questions=assessment_request.open_questions,
                        provider_confidence=ai_response.confidence,
                        context_sections=(
                            initiative_context,
                            payload["context"],
                            payload["manual_content"],
                        ),
                    )
                }
            )
            assessment = await self._assessments.create(
                payload["initiative_id"],
                assessment_request,
                payload["tenant_id"],
                frozenset(payload["workspace_ids"]),
                payload["created_by"],
                job_id=job_id,
                source_context={
                    "submitted_context": payload.get("context", {}),
                    "readiness_dimensions": payload.get("context", {}).get("readiness_dimensions", {}),
                    "manual_content": payload.get("manual_content"),
                },
            )
        except Exception as exc:
            await self._jobs.transition(job_id, JobState.FAILED, error=str(exc))
            return None

        await self._jobs.transition(job_id, JobState.SUCCEEDED)
        return assessment

    async def get_status(
        self,
        job_id: str,
        *,
        tenant_id: str | None = None,
        workspace_ids: set[str] | frozenset[str] | None = None,
    ) -> ReadinessAssessmentJobResponse:
        job = await self._store.get(job_id)
        if job is None:
            raise KeyError(f"Job not found: {job_id}")
        if tenant_id is not None and job.payload.get("tenant_id") != tenant_id:
            raise KeyError(f"Job not found: {job_id}")
        if workspace_ids is not None and not set(job.payload.get("workspace_ids", ())).intersection(workspace_ids):
            raise KeyError(f"Job not found: {job_id}")
        assessment_id = await self._assessment_id_for_job(job)
        return ReadinessAssessmentJobResponse.from_job(job, assessment_id)

    async def retry(self, job_id: str) -> ReadinessAssessmentJobResponse:
        job = await self._jobs.retry(job_id)
        assessment_id = await self._assessment_id_for_job(job)
        return ReadinessAssessmentJobResponse.from_job(job, assessment_id)

    async def _assessment_id_for_job(self, job) -> str | None:
        return await self._assessments.find_id_by_job(
            job.id,
            job.payload["tenant_id"],
            frozenset(job.payload.get("workspace_ids", ())),
        )