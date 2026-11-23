from datetime import UTC, datetime

from app.features.workspaces.domain.entities import Workspace
from app.features.workspaces.schemas.responses import WorkspaceResponse


def test_serializa_workspace_entity() -> None:
    workspace = Workspace(
        id="workspace-1",
        tenant_id="tenant-1",
        name="Product Team",
        description="Core context",
        created_by="user:user-1",
        created_at=datetime.now(UTC),
    )

    response = WorkspaceResponse.model_validate(workspace)

    assert response.id == workspace.id
    assert response.name == workspace.name