from collections.abc import Callable

from fastapi import Depends, HTTPException

from .auth_model import IdentityClaims, UserRole, WorkspaceScope
from .security import get_current_principal


def require_roles(*allowed_roles: UserRole) -> Callable:
    async def dependency(
        principal: IdentityClaims = Depends(get_current_principal),
    ) -> IdentityClaims:
        if not principal.roles.intersection(allowed_roles):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return principal

    return dependency


def require_workspace_scope(workspace_id: str) -> Callable:
    async def dependency(
        principal: IdentityClaims = Depends(get_current_principal),
    ) -> WorkspaceScope:
        if workspace_id not in principal.workspace_ids:
            raise HTTPException(status_code=403, detail="Workspace access denied")
        return WorkspaceScope(tenant_id=principal.tenant_id, workspace_id=workspace_id)

    return dependency


can_approve_ai_proposal = require_roles(UserRole.ADMIN, UserRole.PRODUCT_MANAGER)
