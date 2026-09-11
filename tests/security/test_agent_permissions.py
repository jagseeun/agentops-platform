from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app

client = TestClient(app)

def unique_slug(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"

def auth_headers(role:str, workspace_id: int = 1)->dict[str,str]:
    return {
        "X-User-Id":"1",
        "X-Workspace-Id" : str(workspace_id),
        "X-User-Role" : role,
    }
    
def test_viewer_cannot_create_agent()->None:
    response = client.post(
        "/agents",
        json={"workspace_id":1, "name":"viewer-agent", "version":"1.0.0"},
        headers=auth_headers("viewer"),
    )
    
    assert response.status_code == 403
    
    
def test_developer_cannot_create_agent() -> None:
    response = client.post(
        "/agents",
        json = {"workspace_id":1, "name":"developer_agent", "version":"1.0.0"},
        
        headers=auth_headers("developer"),
    )
    assert response.status_code == 403
    
def test_admin_can_create_agent() -> None:
    workspace_response = client.post(
        "/workspaces",
        json = {"name": "Permission Admin", "slug": unique_slug("permission_admin_workspace_test")},
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]
    
    response = client.post(
        "/agents",
        json = {
            "workspace_id": workspace_id,
            "name": "admin-agent",
            "version": "1.0.0",
        },
        headers=auth_headers("admin", workspace_id=workspace_id),
    )
    assert response.status_code==201
    data=response.json()
    assert data["workspace_id"] == workspace_id
    assert data["name"] == "admin-agent"
    assert data["version"] == "1.0.0"
