from .domain.entities import Product, ProductVersionConflict
from .repository import ProductRepository
from .schemas.requests import CreateProductRequest, UpdateProductRequest


class ProductNotFoundError(LookupError):
    pass


class ProductAccessError(PermissionError):
    pass


class ProductService:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def create(self, request: CreateProductRequest, tenant_id: str, subject: str, workspace_ids: set[str]) -> Product:
        self._check_workspace(request.workspace_id, workspace_ids)
        if request.created_by != subject:
            raise ProductAccessError("created_by must match the authenticated subject")
        product = Product.create(
            workspace_id=request.workspace_id,
            name=request.name,
            created_by=subject,
            description=request.description,
            vision=request.vision,
        )
        await self._repository.insert(tenant_id, product)
        return product

    async def get(self, product_id: str, tenant_id: str) -> Product:
        product = await self._repository.find_by_id(tenant_id, product_id)
        if product is None:
            raise ProductNotFoundError("Product not found")
        return product

    async def list(self, workspace_id: str, tenant_id: str, workspace_ids: set[str]) -> list[Product]:
        self._check_workspace(workspace_id, workspace_ids)
        return await self._repository.list_by_workspace(tenant_id, workspace_id)

    async def update(
        self,
        product_id: str,
        request: UpdateProductRequest,
        tenant_id: str,
        workspace_ids: set[str],
    ) -> Product:
        product = await self.get(product_id, tenant_id)
        self._check_workspace(product.workspace_id, workspace_ids)
        expected_version = request.expected_version
        product.update(
            expected_version=expected_version,
            name=request.name,
            description=request.description,
            vision=request.vision,
        )
        if not await self._repository.replace(tenant_id, product, expected_version):
            raise ProductVersionConflict("Product was modified by another request")
        return product

    @staticmethod
    def _check_workspace(workspace_id: str, workspace_ids: set[str]) -> None:
        if workspace_id not in workspace_ids:
            raise ProductAccessError("Workspace access denied")