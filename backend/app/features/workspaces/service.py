from pymongo.errors import DuplicateKeyError

from ...shared.auth.auth_model import IdentityClaims
from ...shared.auth.identity_repository import IdentityRepository
from .domain.entities import Workspace
from .repository import WorkspaceRepository
from .schemas.requests import CreateWorkspaceRequest


class WorkspaceConflictError(Exception):
    pass


class WorkspaceService:
    def __init__(self, repository: WorkspaceRepository, identities: IdentityRepository) -> None:
        self._repository = repository
        self._identities = identities

    async def create(self, request: CreateWorkspaceRequest, principal: IdentityClaims) -> Workspace:
        if not principal.subject.startswith("user:"):
            raise PermissionError("Only user identities can create workspaces")
        workspace = Workspace.create(principal.tenant_id, request.name.strip(), request.description, principal.subject)
        try:
            await self._repository.insert(workspace)
        except DuplicateKeyError as exc:
            raise WorkspaceConflictError("Workspace name already exists") from exc
        if not await self._identities.add_workspace_to_user(principal.subject, principal.tenant_id, workspace.id):
            raise PermissionError("User identity not found")
        return workspace