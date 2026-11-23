from types import SimpleNamespace

import pytest

from app.features.initiatives.domain.enums import InitiativeStatus
from app.features.initiatives.schemas.requests import CreateInitiativeRequest, UpdateInitiativeRequest
from app.features.initiatives.service import InitiativeConflictError, InitiativeReferenceError, InitiativeService


class FakeRepository:
    def __init__(self):
        self.item = None

    async def insert(self, tenant_id, initiative):
        self.item = initiative

    async def find_by_id(self, tenant_id, initiative_id):
        return self.item if self.item and self.item.id == initiative_id else None

    async def list_by_product(self, tenant_id, workspace_id, product_id):
        return [self.item] if self.item and self.item.product_id == product_id and self.item.workspace_id == workspace_id else []

    async def replace(self, tenant_id, initiative, expected_version):
        if self.item is None or self.item.version != expected_version + 1:
            return False
        self.item = initiative
        return True


class FakeOpportunityRepository:
    async def find_by_id(self, tenant_id, opportunity_id):
        return SimpleNamespace(id=opportunity_id, workspace_id="workspace-1", product_id="product-1")


class FakeProductRepository:
    async def find_by_id(self, tenant_id, product_id):
        return SimpleNamespace(id=product_id, workspace_id="workspace-1")


class FakeProblemRepository:
    async def find_by_id(self, tenant_id, workspace_ids, problem_id):
        return SimpleNamespace(id=problem_id, workspace_id="workspace-1", opportunity_id="opportunity-1", product_id="product-1")


class FakeHypothesisRepository:
    def __init__(self, workspace_id="workspace-1"):
        self.workspace_id = workspace_id

    async def find_by_id(self, tenant_id, hypothesis_id):
        return SimpleNamespace(id=hypothesis_id, workspace_id=self.workspace_id, opportunity_id="opportunity-1")


class FakeObjectiveRepository:
    def __init__(self, workspace_id="workspace-1", product_id="product-1"):
        self.workspace_id = workspace_id
        self.product_id = product_id

    async def find_by_id(self, tenant_id, objective_id):
        return SimpleNamespace(id=objective_id, workspace_id=self.workspace_id, product_id=self.product_id)


def _service(hypothesis_workspace="workspace-1", objective_workspace="workspace-1", objective_product="product-1"):
    repository = FakeRepository()
    return repository, InitiativeService(
        repository,
        FakeProductRepository(),
        FakeOpportunityRepository(),
        FakeProblemRepository(),
        FakeHypothesisRepository(hypothesis_workspace),
        FakeObjectiveRepository(objective_workspace, objective_product),
    )


def _request(**changes):
    values = {
        "title": "Improve onboarding",
        "objective": "Increase completed onboarding",
        "scope": "Guided onboarding flow",
        "problem_id": "problem-1",
        "hypothesis_ids": ["hypothesis-1"],
        "objective_ids": ["objective-1"],
    }
    values.update(changes)
    return CreateInitiativeRequest(**values)


@pytest.mark.asyncio
async def test_cria_validando_referencias_no_mesmo_workspace():
    repository, service = _service()

    result = await service.create("opportunity-1", _request(), "tenant-1", {"workspace-1"}, "user-1")

    assert result.status is InitiativeStatus.DRAFT
    assert result.product_id == "product-1"
    assert repository.item is result
    assert result.objective_ids == ["objective-1"]


@pytest.mark.asyncio
async def test_cria_initiative_com_varios_objectives():
    _, service = _service()

    result = await service.create(
        "opportunity-1",
        _request(objective_ids=["objective-1", "objective-2"]),
        "tenant-1",
        {"workspace-1"},
        "user-1",
    )

    assert result.objective_ids == ["objective-1", "objective-2"]


@pytest.mark.asyncio
async def test_reutiliza_o_mesmo_objective_em_varias_initiatives():
    first_repository, first_service = _service()
    second_repository, second_service = _service()

    first = await first_service.create("opportunity-1", _request(), "tenant-1", {"workspace-1"}, "user-1")
    second = await second_service.create("opportunity-1", _request(title="Improve retention"), "tenant-1", {"workspace-1"}, "user-1")

    assert first_repository.item.objective_ids == ["objective-1"]
    assert second_repository.item.objective_ids == ["objective-1"]
    assert first.id != second.id


@pytest.mark.asyncio
async def test_rejeita_objective_de_outro_product():
    _, service = _service(objective_product="product-2")

    with pytest.raises(InitiativeReferenceError, match="does not belong to the product"):
        await service.create("opportunity-1", _request(), "tenant-1", {"workspace-1"}, "user-1")


@pytest.mark.asyncio
async def test_rejeita_hypothesis_de_outro_workspace():
    _, service = _service(hypothesis_workspace="workspace-2")

    with pytest.raises(InitiativeReferenceError, match="Hypothesis"):
        await service.create("opportunity-1", _request(), "tenant-1", {"workspace-1"}, "user-1")


@pytest.mark.asyncio
async def test_rejeita_objective_de_outro_workspace():
    _, service = _service(objective_workspace="workspace-2")

    with pytest.raises(InitiativeReferenceError, match="Objective"):
        await service.create("opportunity-1", _request(), "tenant-1", {"workspace-1"}, "user-1")


@pytest.mark.asyncio
async def test_patch_rejeita_versao_obsoleta():
    repository, service = _service()
    await service.create("opportunity-1", _request(), "tenant-1", {"workspace-1"}, "user-1")

    with pytest.raises(InitiativeConflictError):
        await service.update(
            repository.item.id,
            UpdateInitiativeRequest(expected_version=2, objective="A different objective"),
            "tenant-1",
            {"workspace-1"},
        )