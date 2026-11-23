from types import SimpleNamespace

import pytest

from app.features.okrs.schemas.requests import CreateKeyResultRequest, CreateObjectiveRequest
from app.features.okrs.service import ObjectiveAccessError, ObjectiveService


class FakeObjectiveRepository:
    async def insert(self, tenant_id, objective):
        self.item = objective

    async def find_by_id(self, tenant_id, objective_id):
        return getattr(self, "item", None)

    async def list_by_workspace(self, tenant_id, workspace_id):
        return []

    async def replace(self, tenant_id, objective):
        self.item = objective


class FakeProductRepository:
    def __init__(self, workspace_id="workspace-1"):
        self.workspace_id = workspace_id

    async def find_by_id(self, tenant_id, product_id):
        return SimpleNamespace(id=product_id, workspace_id=self.workspace_id)


def build_request(**changes):
    values = {
        "title": "Aumentar ativacao",
        "description": "Melhorar a experiencia inicial do produto.",
        "key_results": [CreateKeyResultRequest(metric="Ativacao", target="0.75", due_date="2026-12-31")],
        "product_id": "product-1",
    }
    values.update(changes)
    return CreateObjectiveRequest(**values)


def build_service(product_workspace="workspace-1"):
    return ObjectiveService(
        FakeObjectiveRepository(),
        FakeProductRepository(product_workspace),
    )


@pytest.mark.asyncio
async def test_create_validates_product_context():
    objective = await build_service().create(build_request(), "tenant-1", "workspace-1", {"workspace-1"})

    assert objective.product_id == "product-1"
    assert objective.workspace_id == "workspace-1"


@pytest.mark.asyncio
async def test_create_rejects_product_from_another_workspace():
    with pytest.raises(ObjectiveAccessError, match="Product workspace"):
        await build_service(product_workspace="workspace-2").create(
            build_request(), "tenant-1", "workspace-1", {"workspace-1"}
        )