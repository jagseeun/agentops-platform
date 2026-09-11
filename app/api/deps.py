from fastapi import Depends, Header, HTTPException
from app.core.security import UserContext, UserRole
from collections.abc import Callable

def get_current_user(
    x_user_id : int = Header(alias="X-User-Id"),
    x_workspace_id : int = Header(alias="X-Workspace-Id"),
    x_user_role : UserRole = Header(alias="X-User-Role"),
) -> UserContext:
    return UserContext(
        user_id=x_user_id,
        workspace_id=x_workspace_id,
        role=x_user_role,
    )
    
def require_roles(
    allowed_roles: list[UserRole],
)->Callable[..., UserContext]:
    def dependency(
        current_user: UserContext = Depends(get_current_user),
    )->UserContext:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="forbidden")
        return current_user
    return dependency