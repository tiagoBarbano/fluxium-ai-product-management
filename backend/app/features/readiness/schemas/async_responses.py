from pydantic import BaseModel

from ....shared.jobs import JobRecord, JobState


class ReadinessAssessmentJobResponse(BaseModel):
    job_id: str
    state: JobState
    idempotency_key: str
    correlation_id: str
    retry_count: int
    error: str | None = None
    assessment_id: str | None = None

    @classmethod
    def from_job(cls, job: JobRecord, assessment_id: str | None = None) -> "ReadinessAssessmentJobResponse":
        return cls(
            job_id=job.id,
            state=job.state,
            idempotency_key=job.idempotency_key,
            correlation_id=job.correlation_id,
            retry_count=job.retry_count,
            error=job.error,
            assessment_id=assessment_id,
        )