from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..domain.entities import Product
from ..domain.enums import ProductStatus


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    name: str
    description: str | None
    vision: str | None
    status: ProductStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    version: int

    @classmethod
    def from_entity(cls, product: Product) -> "ProductResponse":
        return cls(
            id=product.id,
            workspace_id=product.workspace_id,
            name=product.name.value,
            description=product.description,
            vision=product.vision,
            status=product.status,
            created_by=product.created_by,
            created_at=product.created_at,
            updated_at=product.updated_at,
            version=product.version,
        )


class ProductListResponse(BaseModel):
    items: list[ProductResponse]