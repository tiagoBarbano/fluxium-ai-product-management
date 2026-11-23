from datetime import UTC, datetime, timedelta

import pytest

from app.features.business_problems.domain.entities import BusinessProblem, BusinessProblemVersionConflict
from app.features.business_problems.domain.enums import BusinessProblemStatus


CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def make_problem() -> BusinessProblem:
    return BusinessProblem.create(
        problem_id="problem-1",
        workspace_id="workspace-1",
        product_id="product-1",
        opportunity_id="opportunity-1",
        description="Customers cannot track claims",
        audience="Claims customers",
        reported_impact="High call volume",
        created_by="user-1",
        now=CREATED_AT,
    )


def test_deve_criar_business_problem_aberto_com_versao_inicial() -> None:
    problem = make_problem()

    assert problem.status is BusinessProblemStatus.OPEN
    assert problem.version == 1
    assert problem.created_at == CREATED_AT
    assert problem.updated_at == CREATED_AT


def test_deve_atualizar_campos_e_incrementar_versao() -> None:
    problem = make_problem()
    updated_at = CREATED_AT + timedelta(hours=1)

    problem.update(
        expected_version=1,
        audience="Enterprise claims customers",
        estimated_impact="20% fewer calls",
        status=BusinessProblemStatus.VALIDATED,
        now=updated_at,
    )

    assert problem.audience == "Enterprise claims customers"
    assert problem.estimated_impact == "20% fewer calls"
    assert problem.status is BusinessProblemStatus.VALIDATED
    assert problem.version == 2
    assert problem.updated_at == updated_at


def test_deve_rejeitar_atualizacao_com_versao_obsoleta() -> None:
    problem = make_problem()

    with pytest.raises(BusinessProblemVersionConflict):
        problem.update(expected_version=2, description="New description")


@pytest.mark.parametrize("field", ["description", "audience", "reported_impact"])
def test_deve_rejeitar_campo_obrigatorio_em_branco(field: str) -> None:
    values = {
        "workspace_id": "workspace-1",
        "product_id": "product-1",
        "opportunity_id": "opportunity-1",
        "description": "Description",
        "audience": "Audience",
        "reported_impact": "Impact",
        "created_by": "user-1",
    }
    values[field] = " "

    with pytest.raises(ValueError):
        BusinessProblem.create(**values)