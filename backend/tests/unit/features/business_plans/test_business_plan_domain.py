from datetime import UTC, datetime

import pytest

from app.features.business_plans.domain.entities import BusinessPlan, BusinessPlanVersionConflict


def test_deve_modelar_5w2h_opcional_e_incrementar_versao() -> None:
    plan = BusinessPlan.create(
        initiative_id="initiative-1",
        workspace_id="workspace-1",
        rationale="Improve claim handling",
        what="Self-service status",
        why="Reduce support volume",
        metrics=["resolution time"],
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    plan.update(expected_version=1, risks=["Low adoption"], now=datetime(2026, 1, 2, tzinfo=UTC))

    assert plan.what == "Self-service status"
    assert plan.when is None
    assert plan.risks == ("Low adoption",)
    assert plan.version == 2


def test_deve_rejeitar_rationale_em_branco_e_versao_obsoleta() -> None:
    with pytest.raises(ValueError):
        BusinessPlan.create(initiative_id="initiative-1", workspace_id="workspace-1", rationale=" ")

    plan = BusinessPlan.create(initiative_id="initiative-1", workspace_id="workspace-1", rationale="Valid")
    with pytest.raises(BusinessPlanVersionConflict):
        plan.update(expected_version=2, rationale="Stale")