from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from ...database.mongo import get_database
from ...shared.auth import IdentityClaims, UserRole
from ...shared.auth.authorization import require_roles
from .repository import MongoProductRepository
from .schemas.requests import CreateProductRequest, UpdateProductRequest
from .schemas.responses import ProductListResponse, ProductResponse
from .domain.entities import ProductVersionConflict
from .service import ProductAccessError, ProductNotFoundError, ProductService


router = APIRouter(prefix="/products", tags=["products"])
write_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR)
read_roles = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER, UserRole.CONTRIBUTOR, UserRole.VIEWER)


def get_product_service() -> ProductService:
    return ProductService(MongoProductRepository(get_database()["products"]))


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: CreateProductRequest,
    principal: IdentityClaims = Depends(write_roles),
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    try:
        product = await service.create(request, principal.tenant_id, principal.subject, principal.workspace_ids)
        return ProductResponse.from_entity(product)
    except ProductAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("", response_model=ProductListResponse)
async def list_products(
    workspace_id: str = Query(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: ProductService = Depends(get_product_service),
) -> ProductListResponse:
    try:
        products = await service.list(workspace_id, principal.tenant_id, principal.workspace_ids)
        return ProductListResponse(items=[ProductResponse.from_entity(product) for product in products])
    except ProductAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ProductVersionConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(read_roles),
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    try:
        product = await service.get(product_id, principal.tenant_id)
        if product.workspace_id not in principal.workspace_ids:
            raise ProductAccessError("Workspace access denied")
        return ProductResponse.from_entity(product)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProductAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    request: UpdateProductRequest,
    product_id: str = Path(min_length=1, max_length=100),
    principal: IdentityClaims = Depends(write_roles),
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    try:
        product = await service.update(product_id, request, principal.tenant_id, principal.workspace_ids)
        return ProductResponse.from_entity(product)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProductAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc