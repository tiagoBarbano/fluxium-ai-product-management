from types import SimpleNamespace

import pytest

from app.features.readiness.domain.entities import ReadinessDimensionScore, calculate_readiness_confidence
from app.features.readiness.schemas.requests import CreateReadinessAssessmentRequest
from app.features.readiness.service import (
    ReadinessAssessmentAccessError,
    ReadinessAssessmentService,
    ReadinessInitiativeNotFoundError,
)


class FakeRepository:
    def __init__(self, workspace_id: str = "workspace-1") -> None:
        self.initiative = SimpleNamespace(
            id="initiative-1", workspace_id=workspace_id, product_id="product-1", opportunity_id="opportunity-1",
            problem_id=None, title="Improve onboarding", objective="Reduce onboarding friction",
            hypothesis_ids=[], objective_ids=[], evidence_ids=[], scope="Onboarding flow",
            out_of_scope=None, status="DRAFT", version=1,
        )
        self.assessments = []
        self.job_assessment_ids = {}

    async def find_initiative(self, tenant_id: str, initiative_id: str):
        return self.initiative if initiative_id == self.initiative.id else None

    async def find_initiative_context(self, tenant_id: str, initiative_id: str):
        return self.initiative if initiative_id == self.initiative.id else None

    async def insert(self, tenant_id: str, assessment, job_id: str | None = None) -> None:
        self.assessments.append(assessment)
        if job_id is not None:
            self.job_assessment_ids[job_id] = assessment.id

    async def find_id_by_job(self, tenant_id: str, workspace_ids: set[str], job_id: str):
        return self.job_assessment_ids.get(job_id)

    async def find_by_id(self, tenant_id: str, workspace_ids: set[str], assessment_id: str):
        return next((item for item in self.assessments if item.id == assessment_id and item.workspace_id in workspace_ids), None)

    async def list_by_initiative(self, tenant_id: str, workspace_ids: set[str], initiative_id: str):
        return [item for item in self.assessments if item.initiative_id == initiative_id and item.workspace_id in workspace_ids]


def _request(**changes) -> CreateReadinessAssessmentRequest:
    dimensions = [
        {"name": "problem", "score": 100, "justification": "Problem is explicit."},
        {"name": "evidence", "score": 90, "justification": "Evidence is documented."},
        {"name": "hypothesis", "score": 80, "justification": "Hypothesis is testable."},
        {"name": "value", "score": 70, "justification": "Value is described."},
        {"name": "kpi", "score": 60, "justification": "KPI is measurable."},
        {"name": "scope", "score": 50, "justification": "Scope is bounded."},
        {"name": "ux", "score": 40, "justification": "UX is partially defined."},
        {"name": "technical_discovery", "score": 30, "justification": "Technical discovery is partial."},
    ]
    values = {"dimensions": dimensions, "confidence": 0.8, "context_version": "initiative-v3"}
    values.update(changes)
    return CreateReadinessAssessmentRequest(**values)


@pytest.mark.asyncio
async def test_calcula_score_ponderado_e_cria_assessment_imutavel() -> None:
    repository = FakeRepository()
    assessment = await ReadinessAssessmentService(repository).create(
        "initiative-1", _request(), "tenant-1", {"workspace-1"}, "user-1"
    )

    assert assessment.score == 67.5
    assert assessment.provider == "manual"
    assert assessment.created_by == "user-1"
    assert len(repository.assessments) == 1
    with pytest.raises(AttributeError):
        assessment.score = 10


@pytest.mark.asyncio
async def test_rejeita_initiative_inexistente() -> None:
    repository = FakeRepository()
    with pytest.raises(ReadinessInitiativeNotFoundError):
        await ReadinessAssessmentService(repository).create(
            "missing", _request(), "tenant-1", {"workspace-1"}, "user-1"
        )


@pytest.mark.asyncio
async def test_rejeita_workspace_sem_acesso() -> None:
    repository = FakeRepository()
    with pytest.raises(ReadinessAssessmentAccessError):
        await ReadinessAssessmentService(repository).create(
            "initiative-1", _request(), "tenant-1", {"workspace-2"}, "user-1"
        )


def test_rejeita_dimensoes_duplicadas_ou_incompletas() -> None:
    with pytest.raises(ValueError, match="exactly once"):
        _request(dimensions=[{"name": "problem", "score": 10, "justification": "Only one."}] * 8)


def test_confianca_estimada_reduz_com_lacunas_e_perguntas_abertas() -> None:
    dimensions = tuple(
        ReadinessDimensionScore(
            name=dimension.name,
            score=dimension.score,
            justification=dimension.justification,
        )
        for dimension in _request().dimensions
    )

    complete = calculate_readiness_confidence(
        dimensions=dimensions,
        missing_information=(),
        open_questions=(),
        provider_confidence=0.8,
        context_sections=({"initiative": "context"}, {"submitted": "context"}, {"draft": "content"}),
    )
    incomplete = calculate_readiness_confidence(
        dimensions=dimensions,
        missing_information=("KPI",),
        open_questions=("Which users?",),
        provider_confidence=0.8,
        context_sections=({"initiative": "context"}, {}, None),
    )

    assert complete == 0.92
    assert incomplete == 0.62