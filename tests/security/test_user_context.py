from app.api.deps import get_current_user

def test_get_current_user_from_headers()->None:
    user = get_current_user(
        x_user_id=1,
        x_workspace_id=2,
        x_user_role="admin",
    )
    assert user.user_id==1
    assert user.workspace_id==2
    assert user.role=="admin"