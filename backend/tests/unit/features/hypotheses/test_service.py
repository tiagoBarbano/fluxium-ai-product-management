from types import SimpleNamespace

import pytest

from app.features.hypotheses.domain.enums import HypothesisStatus
from app.features.hypotheses.schemas.requests import CreateHypothesisRequest, UpdateHypothesisRequest
from app.features.hypotheses.service import HypothesisConflictError, HypothesisReferenceError, HypothesisService


class FakeOpportunityRepository:
    async def find_by_id(self, tenant_id, opportunity_id):
        return SimpleNamespace(id=opportunity_id, workspace_id="workspace-1")


class FakeEvidenceRepository:
    def __init__(self):
        self.items = {
            "evidence-1": SimpleNamespace(workspace_id="workspace-1", opportunity_id="opp-1"),
            "evidence-2": SimpleNamespace(workspace_id="workspace-2", opportunity_id="opp-1"),
        }

    async def find_by_id(self, tenant_id, evidence_id):
        return self.items.get(evidence_id)


class FakeHypothesisRepository:
    def __init__(self):
        self.item = None

    async def insert(self, tenant_id, hypothesis):
        self.item = hypothesis

    async def find_by_id(self, tenant_id, hypothesis_id):
        return self.item if self.item and self.item.id == hypothesis_id else None

    async def replace(self, tenant_id, hypothesis, expected_version):
        if self.item.version != expected_version + 1:
            return False
        self.item = hypothesis
        return True


def _create_request(evidence_ids=None):
    return CreateHypothesisRequest(
        statement="Users will complete onboarding when guided.",
        expected_behavior="Users follow the guided steps.",
        expected_outcome="Completion rate increases.",
        evidence_ids=evidence_ids or [],
        confidence=0.6,
    )


@pytest.mark.asyncio
async def test_cria_hypothesis_com_evidence_do_mesmo_workspace():
    repository = FakeHypothesisRepository()
    service = HypothesisService(repository, FakeOpportunityRepository(), FakeEvidenceRepository())

    result = await service.create("opp-1", _create_request(["evidence-1"]), "tenant-1", {"workspace-1"}, "user-1")

    assert result.status is HypothesisStatus.DRAFT
    assert result.evidence_ids == ["evidence-1"]
    assert result.version == 1


@pytest.mark.asyncio
async def test_rejeita_evidence_de_outro_workspace():
    service = HypothesisService(FakeHypothesisRepository(), FakeOpportunityRepository(), FakeEvidenceRepository())

    with pytest.raises(HypothesisReferenceError):
        await service.create("opp-1", _create_request(["evidence-2"]), "tenant-1", {"workspace-1"}, "user-1")


@pytest.mark.asyncio
async def test_patch_rejeita_versao_obsoleta():
    repository = FakeHypothesisRepository()
    service = HypothesisService(repository, FakeOpportunityRepository(), FakeEvidenceRepository())
    await service.create("opp-1", _create_request(), "tenant-1", {"workspace-1"}, "user-1")

    with pytest.raises(HypothesisConflictError):
        await service.update(
            repository.item.id,
            UpdateHypothesisRequest(expected_version=2, confidence=0.8),
            "tenant-1",
            {"workspace-1"},
        )