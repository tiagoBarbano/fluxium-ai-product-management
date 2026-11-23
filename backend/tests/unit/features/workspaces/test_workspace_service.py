import pytest

from app.features.workspaces.schemas.requests import CreateWorkspaceRequest
from app.features.workspaces.service import WorkspaceService
from app.shared.auth.auth_model import IdentityClaims, UserRole


class FakeWorkspaceRepository:
    def __init__(self) -> None:
        self.items = []

    async def insert(self, workspace) -> None:
        self.items.append(workspace)


class FakeIdentityRepository:
    def __init__(self, updated: bool = True) -> None:
        self.updated = updated
        self.workspace_ids = []

    async def add_workspace_to_user(self, subject: str, tenant_id: str, workspace_id: str) -> bool:
        if self.updated:
            self.workspace_ids.append(workspace_id)
        return self.updated


def _principal(subject: str = "user:user-1") -> IdentityClaims:
    return IdentityClaims(subject=subject, tenant_id="tenant-1", roles=frozenset({UserRole.ADMIN}))


@pytest.mark.asyncio
async def test_cria_workspace_e_concede_acesso_ao_usuario() -> None:
    repository = FakeWorkspaceRepository()
    identities = FakeIdentityRepository()
    workspace = await WorkspaceService(repository, identities).create(
        CreateWorkspaceRequest(name="Product Team", description="Core context"), _principal()
    )

    assert workspace.name == "Product Team"
    assert repository.items == [workspace]
    assert identities.workspace_ids == [workspace.id]


@pytest.mark.asyncio
async def test_rejeita_conta_de_servico() -> None:
    with pytest.raises(PermissionError, match="Only user identities"):
        await WorkspaceService(FakeWorkspaceRepository(), FakeIdentityRepository()).create(
            CreateWorkspaceRequest(name="Service Workspace"), _principal("consumer:consumer-1")
        )