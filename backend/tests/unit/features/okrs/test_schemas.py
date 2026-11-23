from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.features.okrs.schemas.requests import (
    CreateKeyResultRequest,
    CreateObjectiveRequest,
    UpdateObjectiveRequest,
)
from app.features.okrs.schemas.responses import KeyResultResponse, ObjectiveResponse


def test_create_objective_request_accepts_multiple_key_results() -> None:
    request = CreateObjectiveRequest(
        title="Aumentar a ativacao",
        description="Criar uma experiencia inicial mais clara.",
        key_results=[
            CreateKeyResultRequest(
                metric="Ativacao",
                target=Decimal("0.75"),
                due_date=date(2026, 12, 31),
            ),
            CreateKeyResultRequest(
                metric="Retencao",
                target=Decimal("0.60"),
                due_date=date(2026, 12, 31),
            ),
        ],
        product_id="product-1",
    )

    assert len(request.key_results) == 2


def test_create_objective_request_requires_at_least_one_key_result() -> None:
    with pytest.raises(ValidationError):
        CreateObjectiveRequest(
            title="Aumentar a ativacao",
            description="Criar uma experiencia inicial mais clara.",
            key_results=[],
        )


def test_create_objective_request_requires_product_reference() -> None:
    with pytest.raises(ValidationError):
        CreateObjectiveRequest(
            title="Aumentar a ativacao",
            description="Criar uma experiencia inicial mais clara.",
            key_results=[CreateKeyResultRequest(metric="Ativacao", target=Decimal("0.75"), due_date=date(2026, 12, 31))],
        )


def test_create_key_result_request_requires_metric_target_and_due_date() -> None:
    with pytest.raises(ValidationError):
        CreateKeyResultRequest(
            metric="",
            target=None,
            due_date=None,
        )


def test_update_objective_request_allows_partial_updates() -> None:
    request = UpdateObjectiveRequest(title="Novo titulo")

    assert request.title == "Novo titulo"
    assert request.description is None
    assert request.key_results is None


def test_response_schemas_serialize_domain_values() -> None:
    key_result = KeyResultResponse(
        id="kr-1",
        metric="Ativacao",
        target=Decimal("0.75"),
        due_date=date(2026, 12, 31),
    )
    objective = ObjectiveResponse(
        id="objective-1",
        title="Aumentar a ativacao",
        description="Criar uma experiencia inicial mais clara.",
        key_results=[key_result],
    )

    assert objective.key_results[0].target == Decimal("0.75")