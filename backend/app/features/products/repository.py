from typing import Any, Protocol

from pymongo import ASCENDING
from pymongo.asynchronous.collection import AsyncCollection

from .domain.entities import Product
from .domain.enums import ProductStatus
from .domain.value_objects import ProductName


class ProductRepository(Protocol):
    async def ensure_indexes(self) -> None:
        ...

    async def insert(self, tenant_id: str, product: Product) -> None:
        ...

    async def find_by_id(self, tenant_id: str, product_id: str) -> Product | None:
        ...

    async def list_by_workspace(self, tenant_id: str, workspace_id: str) -> list[Product]:
        ...

    async def replace(
        self,
        tenant_id: str,
        product: Product,
        expected_version: int,
    ) -> bool:
        ...


class MongoProductRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("name", ASCENDING)],
            name="ix_products_tenant_workspace_name",
        )

    async def insert(self, tenant_id: str, product: Product) -> None:
        await self._collection.insert_one(self._to_document(tenant_id, product))

    async def find_by_id(self, tenant_id: str, product_id: str) -> Product | None:
        document = await self._collection.find_one({"tenant_id": tenant_id, "id": product_id})
        return self._from_document(document) if document else None

    async def list_by_workspace(self, tenant_id: str, workspace_id: str) -> list[Product]:
        cursor = self._collection.find(
            {"tenant_id": tenant_id, "workspace_id": workspace_id},
            sort=[("created_at", ASCENDING), ("id", ASCENDING)],
        )
        return [self._from_document(document) async for document in cursor]

    async def replace(self, tenant_id: str, product: Product, expected_version: int) -> bool:
        result = await self._collection.replace_one(
            {
                "tenant_id": tenant_id,
                "id": product.id,
                "version": expected_version,
            },
            self._to_document(tenant_id, product),
        )
        return result.modified_count == 1

    @staticmethod
    def _to_document(tenant_id: str, product: Product) -> dict[str, Any]:
        return {
            "id": product.id,
            "tenant_id": tenant_id,
            "workspace_id": product.workspace_id,
            "name": product.name.value,
            "description": product.description,
            "vision": product.vision,
            "status": product.status.value,
            "created_by": product.created_by,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "version": product.version,
        }

    @staticmethod
    def _from_document(document: dict[str, Any]) -> Product:
        return Product(
            id=document["id"],
            workspace_id=document["workspace_id"],
            name=ProductName(document["name"]),
            description=document.get("description"),
            vision=document.get("vision"),
            status=ProductStatus(document["status"]),
            created_by=document["created_by"],
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            version=document["version"],
        )