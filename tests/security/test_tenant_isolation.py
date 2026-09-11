from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app

client = TestClient(app)

def unique_slug(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"

def auth_headers(workspace_id:int, role: str = "admin")->dict[str,str]:
    return {
        "X-User-Id":"1",
        "X-Workspace-Id":str(workspace_id),
        "X-User-Role":role,
    }
def test_workspace_agent_does_not_appear_in_other_workspace_list()->None:
    workspace_one_response = client.post(
        "/workspaces",
        json = {
            "name": "Tenant One",
            "slug" : unique_slug("tenant_one_workspace_test"),
        },
    )
    assert workspace_one_response.status_code==201
    workspace_one_id = workspace_one_response.json()["id"]
    
    workspace_two_response = client.post(
        "/workspaces",
        json={
            "name" : "Tenant Two",
            "slug" : unique_slug("tenant_two_workspace_test")
        },
    )
    assert workspace_two_response.status_code == 201
    workspace_two_id = workspace_two_response.json()["id"]
    
    agent_one_response = client.post(
        "/agents",
        json={
            "workspace_id" : workspace_one_id,
            "name":"tenant-agent-one",
            "version" : "1.0.0",
        },
        headers = auth_headers(workspace_id = workspace_one_id, role = "admin"),
        
    )
    assert agent_one_response.status_code == 201
    
    agent_two_response = client.post(
        "/agents",
        json={
            "workspace_id" : workspace_two_id,
            "name" : "tenant-agent-two",
            "version":"1.0.0",
        },
        headers = auth_headers(workspace_id = workspace_two_id, role = "admin"),
    )
    assert agent_two_response.status_code==201
    
    list_response = client.get(
        f"/workspaces/{workspace_two_id}/agents",
        headers=auth_headers(workspace_id=workspace_two_id, role = "viewer"),
    )
    assert list_response.status_code==200
    
    data = list_response.json()
    agent_names = [agent["name"] for agent in data]
    
    assert "tenant-agent-two" in agent_names
    assert "tenant-agent-one" not in agent_names 
    
def test_other_workspace_agent_deactivate_returns_404() -> None:
    workspace_one_response = client.post(
        "/workspaces",
        json = {
            "name" : "Deactivate Tenant One",
            "slug" : unique_slug("deactivate_tenant_one_workspace_test"),
        },
    )
    assert workspace_one_response.status_code == 201
    workspace_one_id = workspace_one_response.json()["id"]
    
    workspace_two_response = client.post(
        "/workspaces",
        json = {
            "name":"Deactivate Tenant Two",
            "slug" : unique_slug("deactivate_tenant_two_workspace_test"),
        },
    )
    assert workspace_two_response.status_code==201
    workspace_two_id = workspace_two_response.json()["id"]
    
    agent_response = client.post(
        "/agents",
        json = {
            "workspace_id" : workspace_one_id,
            "name" : "tenant-deactivate-agent",
            "version" : "1.0.0",
        },
        headers = auth_headers(workspace_id = workspace_one_id,role="admin"),
    )
    assert agent_response.status_code == 201
    agent_id = agent_response.json()["id"]
    
    response = client.post(
        f"/workspaces/{workspace_two_id}/agents/{agent_id}/deactivate",
        headers = auth_headers(workspace_id = workspace_two_id, role = "admin")
    )
    assert response.status_code == 404
    
