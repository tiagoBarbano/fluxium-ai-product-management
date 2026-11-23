from datetime import UTC, datetime, timedelta

import pytest

from app.features.products.domain.entities import Product, ProductVersionConflict
from app.features.products.domain.enums import ProductStatus


CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def make_product() -> Product:
    return Product.create(
        product_id="product-1",
        workspace_id="workspace-1",
        name="  Claims Portal  ",
        description="Customer self-service",
        vision="Make claims simple",
        created_by="user-1",
        now=CREATED_AT,
    )


def test_deve_criar_product_ativo_com_versao_inicial() -> None:
    product = make_product()

    assert product.name.value == "Claims Portal"
    assert product.status is ProductStatus.ACTIVE
    assert product.version == 1
    assert product.created_at == CREATED_AT
    assert product.updated_at == CREATED_AT


@pytest.mark.parametrize("name", ["", "   ", "x" * 121])
def test_deve_rejeitar_nome_invalido(name: str) -> None:
    with pytest.raises(ValueError):
        Product.create(
            workspace_id="workspace-1",
            name=name,
            created_by="user-1",
            now=CREATED_AT,
        )


def test_deve_atualizar_e_incrementar_versao() -> None:
    product = make_product()
    updated_at = CREATED_AT + timedelta(hours=1)

    product.update(
        expected_version=1,
        name="Claims Hub",
        vision="Resolve claims faster",
        now=updated_at,
    )

    assert product.name.value == "Claims Hub"
    assert product.vision == "Resolve claims faster"
    assert product.version == 2
    assert product.updated_at == updated_at


def test_deve_rejeitar_atualizacao_com_versao_obsoleta() -> None:
    product = make_product()

    with pytest.raises(ProductVersionConflict):
        product.update(expected_version=2, name="New name")

    assert product.name.value == "Claims Portal"
    assert product.version == 1


def test_deve_transicionar_entre_active_e_archived() -> None:
    product = make_product()

    product.archive(expected_version=1)
    assert product.status is ProductStatus.ARCHIVED
    assert product.version == 2

    with pytest.raises(ValueError, match="already archived"):
        product.archive(expected_version=2)
    with pytest.raises(ValueError, match="cannot be updated"):
        product.update(expected_version=2, name="Cannot update")

    product.activate(expected_version=2)
    assert product.status is ProductStatus.ACTIVE
    assert product.version == 3
