from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.features.products.router import get_product_service
from app.main import create_app
from app.shared.auth.auth_model import IdentityClaims, UserRole
from app.shared.auth.security import get_current_principal


def _principal(role: UserRole) -> IdentityClaims:
    return IdentityClaims(
        subject="user-1",
        tenant_id="tenant-1",
        workspace_ids={"workspace-1"},
        roles={role},
    )


class FakeProductService:
    async def create(self, request, tenant_id, subject, workspace_ids):
        from app.features.products.domain.entities import Product

        return Product.create(
            workspace_id=request.workspace_id,
            name=request.name,
            created_by=subject,
            now=datetime.now(UTC),
        )


def test_product_create_returns_created_product():
    application = create_app()
    application.dependency_overrides[get_current_principal] = lambda: _principal(UserRole.PRODUCT_MANAGER)
    application.dependency_overrides[get_product_service] = FakeProductService

    response = TestClient(application).post(
        "/api/v1/products",
        json={
            "workspace_id": "workspace-1",
            "name": "Core Product",
            "created_by": "user-1",
        },
    )

    assert response.status_code == 201
    assert response.json()["workspace_id"] == "workspace-1"
    assert response.json()["created_by"] == "user-1"


def test_viewer_cannot_create_product():
    application = create_app()
    application.dependency_overrides[get_current_principal] = lambda: _principal(UserRole.VIEWER)

    response = TestClient(application).post(
        "/api/v1/products",
        json={
            "workspace_id": "workspace-1",
            "name": "Core Product",
            "created_by": "user-1",
        },
    )

    assert response.status_code == 403