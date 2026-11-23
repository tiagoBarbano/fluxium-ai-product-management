import pytest

from app.features.business_problems.domain.entities import BusinessProblem
from app.features.business_problems.domain.enums import BusinessProblemStatus
from app.features.business_problems.schemas.requests import CreateBusinessProblemRequest, UpdateBusinessProblemRequest
from app.features.business_problems.service import (
    BusinessProblemAccessError,
    BusinessProblemOpportunityNotFoundError,
    BusinessProblemService,
)
from app.features.opportunities.domain.entities import Opportunity


class FakeOpportunityRepository:
    def __init__(self, opportunity: Opportunity | None) -> None:
        self.opportunity = opportunity

    async def find_by_id(self, tenant_id: str, opportunity_id: str) -> Opportunity | None:
        if tenant_id != "tenant-1" or self.opportunity is None or self.opportunity.id != opportunity_id:
            return None
        return self.opportunity


class FakeBusinessProblemRepository:
    def __init__(self) -> None:
        self.problems: dict[tuple[str, str], BusinessProblem] = {}

    async def ensure_indexes(self) -> None:
        return None

    async def insert(self, tenant_id: str, problem: BusinessProblem) -> None:
        self.problems[(tenant_id, problem.id)] = problem

    async def find_by_id(self, tenant_id: str, workspace_ids: set[str], problem_id: str) -> BusinessProblem | None:
        problem = self.problems.get((tenant_id, problem_id))
        return problem if problem and problem.workspace_id in workspace_ids else None

    async def replace(self, tenant_id: str, problem: BusinessProblem, expected_version: int) -> bool:
        current = self.problems.get((tenant_id, problem.id))
        if current is None or problem.version != expected_version + 1:
            return False
        self.problems[(tenant_id, problem.id)] = problem
        return True


def make_service() -> tuple[BusinessProblemService, FakeBusinessProblemRepository]:
    opportunity = Opportunity(
        id="opportunity-1",
        product_id="product-1",
        title="Claims tracking",
        description="Customers cannot track claims",
        workspace_id="workspace-1",
    )
    repository = FakeBusinessProblemRepository()
    return BusinessProblemService(repository, FakeOpportunityRepository(opportunity)), repository


@pytest.mark.asyncio
async def test_deve_criar_problem_derivando_product_e_workspace_da_opportunity() -> None:
    service, repository = make_service()

    problem = await service.create(
        "opportunity-1",
        CreateBusinessProblemRequest(
            description="Customers cannot track claims",
            audience="Claims customers",
            reported_impact="High call volume",
        ),
        "tenant-1",
        "user-1",
        {"workspace-1"},
    )

    assert problem.product_id == "product-1"
    assert problem.workspace_id == "workspace-1"
    assert repository.problems[("tenant-1", problem.id)] is problem


@pytest.mark.asyncio
async def test_deve_rejeitar_opportunity_inexistente() -> None:
    service, _ = make_service()

    with pytest.raises(BusinessProblemOpportunityNotFoundError):
        await service.create(
            "missing",
            CreateBusinessProblemRequest(
                description="Description",
                audience="Audience",
                reported_impact="Impact",
            ),
            "tenant-1",
            "user-1",
            {"workspace-1"},
        )


@pytest.mark.asyncio
async def test_deve_rejeitar_opportunity_fora_do_workspace_autorizado() -> None:
    service, _ = make_service()

    with pytest.raises(BusinessProblemAccessError):
        await service.create(
            "opportunity-1",
            CreateBusinessProblemRequest(
                description="Description",
                audience="Audience",
                reported_impact="Impact",
            ),
            "tenant-1",
            "user-1",
            {"workspace-other"},
        )


@pytest.mark.asyncio
async def test_deve_atualizar_com_versionamento_otimista() -> None:
    service, _ = make_service()
    problem = await service.create(
        "opportunity-1",
        CreateBusinessProblemRequest(
            description="Description",
            audience="Audience",
            reported_impact="Impact",
        ),
        "tenant-1",
        "user-1",
        {"workspace-1"},
    )

    updated = await service.update(
        problem.id,
        UpdateBusinessProblemRequest(expected_version=1, status=BusinessProblemStatus.VALIDATED),
        "tenant-1",
        {"workspace-1"},
    )

    assert updated.status is BusinessProblemStatus.VALIDATED
    assert updated.version == 2