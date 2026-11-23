from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.features.products.domain.entities import Product
from app.features.products.domain.enums import ProductStatus
from app.features.products.schemas.requests import (
    CreateProductRequest,
    UpdateProductRequest,
)
from app.features.products.schemas.responses import ProductResponse


def test_deve_validar_request_de_criacao_e_normalizar_texto() -> None:
    request = CreateProductRequest(
        workspace_id=" workspace-1 ",
        name=" Claims Portal ",
        description=" Customer self-service ",
        created_by=" user-1 ",
    )

    assert request.workspace_id == "workspace-1"
    assert request.name == "Claims Portal"
    assert request.description == "Customer self-service"
    assert request.vision is None


@pytest.mark.parametrize(
    "payload",
    [
        {"workspace_id": "workspace-1", "name": "", "created_by": "user-1"},
        {"workspace_id": "workspace-1", "name": "Product", "created_by": ""},
        {"workspace_id": "", "name": "Product", "created_by": "user-1"},
    ],
)
def test_deve_rejeitar_request_de_criacao_invalido(payload: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        CreateProductRequest(**payload)


def test_deve_exigir_campo_mutavel_no_request_de_atualizacao() -> None:
    with pytest.raises(ValidationError, match="At least one Product field"):
        UpdateProductRequest(expected_version=1)


def test_deve_serializar_response_a_partir_da_entidade() -> None:
    product = Product.create(
        product_id="product-1",
        workspace_id="workspace-1",
        name="Claims Portal",
        created_by="user-1",
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    response = ProductResponse.from_entity(product)

    assert response.id == "product-1"
    assert response.name == "Claims Portal"
    assert response.status is ProductStatus.ACTIVE
    assert response.version == 1