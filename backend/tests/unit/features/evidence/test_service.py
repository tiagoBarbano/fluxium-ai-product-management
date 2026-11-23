from types import SimpleNamespace

import pytest

from app.features.evidence.domain.entities import Evidence
from app.features.evidence.domain.enums import EvidenceOrigin, EvidenceType
from app.features.evidence.schemas.requests import CreateEvidenceRequest
from app.features.evidence.service import EvidenceReferenceError, EvidenceService


class FakeOpportunityRepository:
    def __init__(self, opportunity):
        self.opportunity = opportunity

    async def find_by_id(self, tenant_id, opportunity_id):
        return self.opportunity if opportunity_id == self.opportunity.id else None


class FakeReferenceRepository:
    def __init__(self, references):
        self.references = references

    async def find_by_id(self, tenant_id, reference_id):
        return self.references.get(reference_id)


class FakeEvidenceRepository:
    def __init__(self):
        self.items = []

    async def insert(self, tenant_id, evidence):
        self.items.append(evidence)


@pytest.mark.asyncio
async def test_cria_evidence_no_workspace_do_opportunity():
    opportunity = SimpleNamespace(id="opp-1", workspace_id="workspace-1")
    repository = FakeEvidenceRepository()
    service = EvidenceService(
        repository,
        FakeOpportunityRepository(opportunity),
        FakeReferenceRepository({"problem-1": SimpleNamespace(workspace_id="workspace-1", opportunity_id="opp-1")}),
    )

    result = await service.create(
        "opp-1",
        CreateEvidenceRequest(
            opportunity_id="opp-1",
            type=EvidenceType.INTERVIEW,
            origin=EvidenceOrigin.MANUAL,
            description="Users abandon the flow before completion.",
            problem_id="problem-1",
        ),
        "tenant-1",
        {"workspace-1"},
        "user-1",
    )

    assert isinstance(result, Evidence)
    assert result.workspace_id == "workspace-1"
    assert repository.items == [result]


@pytest.mark.asyncio
async def test_rejeita_problem_de_outro_workspace():
    opportunity = SimpleNamespace(id="opp-1", workspace_id="workspace-1")
    service = EvidenceService(
        FakeEvidenceRepository(),
        FakeOpportunityRepository(opportunity),
        FakeReferenceRepository({"problem-2": SimpleNamespace(workspace_id="workspace-2", opportunity_id="opp-1")}),
    )

    with pytest.raises(EvidenceReferenceError):
        await service.create(
            "opp-1",
            CreateEvidenceRequest(
                opportunity_id="opp-1",
                type=EvidenceType.DOCUMENT,
                origin=EvidenceOrigin.IMPORTED,
                description="Imported note.",
                problem_id="problem-2",
            ),
            "tenant-1",
            {"workspace-1"},
            "user-1",
        )


@pytest.mark.asyncio
async def test_cria_evidence_com_hypothesis_do_mesmo_workspace():
    opportunity = SimpleNamespace(id="opp-1", workspace_id="workspace-1")
    repository = FakeEvidenceRepository()
    service = EvidenceService(
        repository,
        FakeOpportunityRepository(opportunity),
        hypotheses=FakeReferenceRepository(
            {"hypothesis-1": SimpleNamespace(workspace_id="workspace-1", opportunity_id="opp-1")}
        ),
    )

    result = await service.create(
        "opp-1",
        CreateEvidenceRequest(
            opportunity_id="opp-1",
            type=EvidenceType.EXPERIMENT,
            origin=EvidenceOrigin.OBSERVED,
            description="The guided flow was completed in the experiment.",
            hypothesis_id="hypothesis-1",
        ),
        "tenant-1",
        {"workspace-1"},
        "user-1",
    )

    assert result.hypothesis_id == "hypothesis-1"