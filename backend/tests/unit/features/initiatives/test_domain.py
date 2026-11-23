from datetime import UTC, datetime

import pytest

from app.features.initiatives.domain.entities import Initiative
from app.features.initiatives.domain.enums import InitiativeStatus


def _initiative() -> Initiative:
    return Initiative.create(
        workspace_id="workspace-1",
        product_id="product-1",
        opportunity_id="opportunity-1",
        title="Improve onboarding",
        objective="Increase completed onboarding",
        scope="Guided onboarding flow",
        created_by="user-1",
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_cria_initiative_com_status_e_versao_iniciais():
    initiative = _initiative()

    assert initiative.status is InitiativeStatus.DRAFT
    assert initiative.version == 1
    assert initiative.created_at.tzinfo is not None


def test_rejeita_confidence_fora_do_intervalo():
    with pytest.raises(ValueError, match="outcome_confidence"):
        Initiative.create(
            workspace_id="workspace-1",
            product_id="product-1",
            opportunity_id="opportunity-1",
            title="Improve onboarding",
            objective="Increase completed onboarding",
            scope="Guided onboarding flow",
            created_by="user-1",
            outcome_confidence=1.1,
        )


def test_update_exige_expected_version_e_incrementa_versao():
    initiative = _initiative()

    with pytest.raises(ValueError, match="Expected Initiative version"):
        initiative.update(expected_version=2, title="New title")

    initiative.update(expected_version=1, title="New title")
    assert initiative.title == "New title"
    assert initiative.version == 2