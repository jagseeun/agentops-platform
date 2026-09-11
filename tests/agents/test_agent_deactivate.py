from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app

client = TestClient(app)

def unique_slug(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"

def auth_headers(workspace_id: int, role: str = "admin") -> dict[str, str]:
    return {
        "X-User-Id": "1",
        "X-Workspace-Id": str(workspace_id),
        "X-User-Role": role,
    }

def test_deactivate_agent()->None:
    workspace_response = client.post(
        "/workspaces",
        json={"name": "Deactivate", "slug" : unique_slug("deactivate_workspace_test")},
    )
    assert workspace_response.status_code==201
    workspace_id=workspace_response.json()["id"]
    
    agent_response = client.post(
        "/agents",
        json={
            "workspace_id" : workspace_id,
            "name":"deactivate-agent",
            "version": "1.0.0",
        },
        headers=auth_headers(workspace_id),
    )
    
    assert agent_response.status_code==201
    agent_id = agent_response.json()["id"]
    
    deactivate_response = client.post(
        f"/workspaces/{workspace_id}/agents/{agent_id}/deactivate",
        headers=auth_headers(workspace_id),
        
    )
    assert deactivate_response.status_code==200
    data=deactivate_response.json()
    assert data["id"] == agent_id
    assert data["workspace_id"] == workspace_id
    assert data["status"] == "inactive"
    
    
def test_deactivate_other_workspace_agent_returns_404() -> None:
    workspace_a_response = client.post(
        "/workspaces",
        json={"name": "Deactivate A", "slug": unique_slug("deactivate_workspace_a_test")},
    )
    assert workspace_a_response.status_code==201
    workspace_a_id = workspace_a_response.json()["id"]
    
    workspace_b_response = client.post(
        "/workspaces",
        json ={"name":"Deactivate B", "slug": unique_slug("deactivate_workspace_b_test")},
    )
    assert workspace_b_response.status_code==201
    workspace_b_id = workspace_b_response.json()["id"]
    
    agent_response = client.post(
        "/agents",
        json={
            "workspace_id" : workspace_b_id,
            "name" : "other-workspace-agent",
            "version" : "1.0.0",
        },
        headers=auth_headers(workspace_b_id),
    )
    assert agent_response.status_code==201
    agent_id = agent_response.json()["id"]
    
    deactivate_response = client.post(
        f"/workspaces/{workspace_a_id}/agents/{agent_id}/deactivate",
        headers=auth_headers(workspace_a_id),
    )
    
    assert deactivate_response.status_code == 404
