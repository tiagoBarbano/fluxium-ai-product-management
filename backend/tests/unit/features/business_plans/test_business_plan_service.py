import pytest

from app.features.business_plans.domain.entities import BusinessPlan, BusinessPlanVersionConflict
from app.features.business_plans.domain.models import InitiativeReference
from app.features.business_plans.schemas.requests import UpdateBusinessPlanRequest
from app.features.business_plans.service import (
    BusinessPlanAccessError,
    BusinessPlanInitiativeNotFoundError,
    BusinessPlanService,
)


class FakeBusinessPlanRepository:
    def __init__(self, initiative: InitiativeReference | None) -> None:
        self.initiative = initiative
        self.plan: BusinessPlan | None = None

    async def find_initiative(self, tenant_id: str, initiative_id: str) -> InitiativeReference | None:
        return self.initiative if tenant_id == "tenant-1" and self.initiative and self.initiative.id == initiative_id else None

    async def find_by_initiative(self, tenant_id: str, workspace_ids: set[str], initiative_id: str) -> BusinessPlan | None:
        return self.plan if self.plan and self.plan.initiative_id == initiative_id and self.plan.workspace_id in workspace_ids else None

    async def insert(self, tenant_id: str, plan: BusinessPlan) -> None:
        self.plan = plan

    async def replace(self, tenant_id: str, plan: BusinessPlan, expected_version: int) -> bool:
        if self.plan is None or self.plan.version != expected_version + 1:
            return False
        self.plan = plan
        return True


def make_service() -> tuple[BusinessPlanService, FakeBusinessPlanRepository]:
    repository = FakeBusinessPlanRepository(InitiativeReference("initiative-1", "workspace-1"))
    return BusinessPlanService(repository), repository


@pytest.mark.asyncio
async def test_deve_criar_business_plan_para_initiative_existente() -> None:
    service, repository = make_service()

    plan = await service.update(
        "initiative-1",
        UpdateBusinessPlanRequest(expected_version=0, rationale="Reduce claim handling time", metrics=["time to resolution"]),
        "tenant-1",
        {"workspace-1"},
    )

    assert plan.workspace_id == "workspace-1"
    assert plan.version == 1
    assert repository.plan is plan


@pytest.mark.asyncio
async def test_deve_rejeitar_initiative_inexistente_e_workspace_nao_autorizado() -> None:
    service, _ = make_service()

    with pytest.raises(BusinessPlanInitiativeNotFoundError):
        await service.get("missing", "tenant-1", {"workspace-1"})
    with pytest.raises(BusinessPlanAccessError):
        await service.get("initiative-1", "tenant-1", {"workspace-other"})


@pytest.mark.asyncio
async def test_deve_aplicar_conflito_otimista_no_update() -> None:
    service, _ = make_service()
    await service.update(
        "initiative-1", UpdateBusinessPlanRequest(expected_version=0, rationale="Initial rationale"), "tenant-1", {"workspace-1"}
    )

    with pytest.raises(BusinessPlanVersionConflict):
        await service.update(
            "initiative-1", UpdateBusinessPlanRequest(expected_version=0, rationale="Stale update"), "tenant-1", {"workspace-1"}
        )