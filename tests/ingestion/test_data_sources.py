from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def auth_headers(workspace_id: int, role: str = "admin")->dict[str, str]:
    return {
        "X-User-Id": "1",
        "X-Workspace-Id":str(workspace_id),
        "X-User-Role": role,
    }

def unique_slug(prefix: str)-> str:
    return f"{prefix}_{uuid4().hex}"

def create_workspace(name: str)->int:
    response = client.post(
        "/workspaces",
        json={"name":name, "slug":unique_slug(name.lower())},
    )
    assert response.status_code == 201
    return response.json()["id"]

def upload_data_source(
    workspace_id : int,
    *,
    role: str = "admin",
    content: str = "Long test...",
):
    return client.post(
        f"/workspaces/{workspace_id}/data-sources",
        json = {
            "name" : "sample-policy.txt",
            "content": content,
        },
        headers=auth_headers(workspace_id=workspace_id, role=role),
    )
    
def test_admin_can_upload_data_source()->None:
    workspace_id = create_workspace("Ingestion Admin")
    response = upload_data_source(workspace_id, role="admin")
    
    assert response.status_code == 201
    data = response.json()
    assert data["workspace_id"] == workspace_id
    assert data["name"] == "sample-policy.txt"
    assert data["status"] == "completed"
    assert data["error_message"] is None
    
def test_developer_can_upload_data_source()->None:
    workspace_id = create_workspace("Ingestion Developer")
    response = upload_data_source(workspace_id, role="developer")
    
    assert response.status_code == 201
    assert response.json()["status"] == "completed"
    
def test_viewer_cannot_upload_data_source()->None:
    workspace_id = create_workspace("Ingestion Viewer")
    response = upload_data_source(workspace_id, role="viewer")
    
    assert response.status_code == 403
    
def test_upload_data_source_requires_content()->None:
    workspace_id = create_workspace("Ingestion Empty Content")
    
    response = upload_data_source(
        workspace_id,
        role="admin",
        content = "",
    )