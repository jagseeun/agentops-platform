from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app

from sqlalchemy import func
from app.db.session import SessionLocal
from app.models.workspace import Workspace

client = TestClient(app)

def unique_slug(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"

def auth_headers(workspace_id: int, role: str = "admin") -> dict[str, str]:
    return {
        "X-User-Id": "1",
        "X-Workspace-Id": str(workspace_id),
        "X-User-Role": role,
    }

def test_create_agents()->None:
    workspace_response = client.post(
        "/workspaces",
        json={"name":"Create", "slug": unique_slug("create")}
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"] 
    response = client.post(
        "/agents",
        json={"workspace_id" : workspace_id, "name":"SeeunAGT", "version": "1.0.1"},
        headers=auth_headers(workspace_id),
    )
    assert response.status_code == 201
    
    response = client.post(
        "/agents",
        json={"workspace_id" : workspace_id, "name":"SeeunAGT", "version": "1.0.1"},
        headers=auth_headers(workspace_id),
    )
    assert response.status_code == 409

def test_existing_workspace_id() -> None:
    with SessionLocal() as db:
        max_workspace_id = (
            db.query(func.max(Workspace.id)).scalar() or 0
        )
    nonexistent_workspace_id = max_workspace_id + 1
    
    response = client.post(
        "/agents",
        json = {
            "workspace_id" : nonexistent_workspace_id,
            "name":"over",
            "version" : "1000.0.1",
        },
        headers = auth_headers(nonexistent_workspace_id),
    )
    assert response.status_code == 404 
        
def test_another_workspace()->None:
    
    workspace_first_response = client.post(
        "/workspaces",
        json={"name":"First", "slug": unique_slug("first_workspace_test")}
    )
    assert workspace_first_response.status_code == 201
    workspace_first = workspace_first_response.json()["id"] 
    
    workspace_second_response = client.post(
        "/workspaces",
        json={"name":"Second", "slug": unique_slug("second_workspace_test")}
    )
    assert workspace_second_response.status_code == 201
    workspace_second = workspace_second_response.json()["id"] 
    
    response1 = client.post(
        "/agents",
        json={"workspace_id" : workspace_first, "name":"agent", "version": "1.1.1"},
        headers=auth_headers(workspace_first),
    )
    assert response1.status_code == 201
    response2 = client.post(
        "/agents",
        json={"workspace_id" : workspace_second, "name":"agent", "version": "1.1.1"},
        headers=auth_headers(workspace_second),
    )
    assert response2.status_code == 201
    
def test_list_agents_by_workspace() -> None:
    workspace_response = client.post(
        "/workspaces",
        json={"name":"List", "slug": unique_slug("list_workspace_test")},
    )
    assert workspace_response.status_code==201
    workspace_id=workspace_response.json()["id"]
    
    other_workspace_response = client.post(
        "/workspaces",
        json={"name": "Other List", "slug": unique_slug("other_list_workspace_test")},
    )
    assert other_workspace_response.status_code == 201
    other_workspace_id = other_workspace_response.json()["id"]
    
    response1=client.post(
        "/agents",
        json={
            "workspace_id": workspace_id,
            "name" : "list-agent",
            "version" : "1.0.1",
        },
        headers=auth_headers(workspace_id),
    )
    assert response1.status_code == 201
    
    response2 = client.post(
        "/agents",
        json={
            "workspace_id" : other_workspace_id,
            "name" : "other-list-agent",
            "version" : "1.0.0",
        },
        headers=auth_headers(other_workspace_id),
    )
    assert response2.status_code==201
    
    list_response=client.get(
        f"/workspaces/{workspace_id}/agents",
        headers=auth_headers(workspace_id, role="viewer"),
    )
    assert list_response.status_code == 200
    
    data = list_response.json()
    assert len(data)==1
    assert data[0]["workspace_id"] == workspace_id
    assert data[0]["name"] == "list-agent"
    
    
def test_list_agents_by_active_status() -> None:
    workspace_response = client.post(
        "/workspaces",
        json = {"name": "Status", "slug": unique_slug("status_workspace_test")},
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]
        
    response = client.post(
        "/agents",
        json = {
        "workspace_id" : workspace_id,
        "name" : "status-agent",
        "version" : "1.0.0",
        },
        headers=auth_headers(workspace_id),
    )
    assert response.status_code == 201
        
    list_response = client.get(
        f"/workspaces/{workspace_id}/agents?status=active",
        headers=auth_headers(workspace_id, role="viewer"),
    )
    assert list_response.status_code == 200
        
    data = list_response.json()
        
    assert len(data)==1
        
    assert data[0]["status"] == "active"
    assert data[0]["workspace_id"]==workspace_id
    assert data[0]["name"] == "status-agent"
    
    print(list_response.json())
