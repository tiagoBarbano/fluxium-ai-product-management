import pytest

from app.features.products.domain.entities import Product, ProductVersionConflict
from app.features.products.schemas.requests import CreateProductRequest, UpdateProductRequest
from app.features.products.service import ProductAccessError, ProductService


class FakeProductRepository:
    def __init__(self) -> None:
        self.products = {}

    async def ensure_indexes(self) -> None:
        return None

    async def insert(self, tenant_id, product):
        self.products[(tenant_id, product.id)] = product

    async def find_by_id(self, tenant_id, product_id):
        return self.products.get((tenant_id, product_id))

    async def list_by_workspace(self, tenant_id, workspace_id):
        return [
            product
            for (stored_tenant, _), product in self.products.items()
            if stored_tenant == tenant_id and product.workspace_id == workspace_id
        ]

    async def replace(self, tenant_id, product, expected_version):
        current = self.products.get((tenant_id, product.id))
        if current is None or product.version != expected_version + 1:
            return False
        self.products[(tenant_id, product.id)] = product
        return True


@pytest.fixture
def service() -> ProductService:
    return ProductService(FakeProductRepository())


@pytest.mark.asyncio
async def test_create_and_update_product_with_authorized_workspace(service):
    product = await service.create(
        CreateProductRequest(
            workspace_id="workspace-1",
            name="Core Product",
            created_by="user-1",
        ),
        "tenant-1",
        "user-1",
        {"workspace-1"},
    )

    updated = await service.update(
        product.id,
        UpdateProductRequest(expected_version=1, name="Updated Product"),
        "tenant-1",
        {"workspace-1"},
    )

    assert updated.name.value == "Updated Product"
    assert updated.version == 2


@pytest.mark.asyncio
async def test_product_rejects_workspace_outside_principal_scope(service):
    with pytest.raises(ProductAccessError):
        await service.create(
            CreateProductRequest(
                workspace_id="workspace-other",
                name="Forbidden Product",
                created_by="user-1",
            ),
            "tenant-1",
            "user-1",
            {"workspace-1"},
        )


@pytest.mark.asyncio
async def test_product_update_rejects_stale_version(service):
    product = await service.create(
        CreateProductRequest(
            workspace_id="workspace-1",
            name="Core Product",
            created_by="user-1",
        ),
        "tenant-1",
        "user-1",
        {"workspace-1"},
    )
    await service.update(
        product.id,
        UpdateProductRequest(expected_version=1, name="First Update"),
        "tenant-1",
        {"workspace-1"},
    )

    with pytest.raises(ProductVersionConflict):
        await service.update(
            product.id,
            UpdateProductRequest(expected_version=1, name="Stale Update"),
            "tenant-1",
            {"workspace-1"},
        )