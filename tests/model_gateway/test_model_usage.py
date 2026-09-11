from uuid import uuid4
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.repositories.model_call_repository import ModelCallRepository

client = TestClient(app)

def unique_slug(prefix : str) -> str:
    return f"{prefix}_{uuid4().hex}"

def auth_headers(workspace_id : int, role: str = "viewer")->dict[str,str]:
    return {
        "X-User-Id": "1",
        "X-Workspace-Id" : str(workspace_id),
        "X-User-Role" : role,
    }
def create_workspace()->int:
    response = client.post(
        "/workspaces",
        json={
            "name": "Usage Summary",
            "slug" : unique_slug("usage_summary"),
        },
    )
    assert response.status_code == 201
    return response.json()["id"]

def create_model_call(
    *, workspace_id : int, status : str, latency_ms : int,
)->None:
    db = SessionLocal()
    
    try:
        repository = ModelCallRepository(db)
        repository.create(
            workspace_id=workspace_id,
            run_id = None,
            provider="fake",
            model_name="fake-model",
            prompt_tokens = 3,
            completion_tokens=4,
            latency_ms=latency_ms,
            estimated_cost=0,
            status = status,
        )
    finally:
        db.close()
        
def test_get_model_call_usage_summary()->None:
    workspace_id= create_workspace()
    create_model_call(
        workspace_id = workspace_id,
        status = "success",
        latency_ms = 100,
    )
    create_model_call(
        workspace_id = workspace_id,
        status = "success",
        latency_ms=300,
    )
    create_model_call(
        workspace_id = workspace_id,
        status = "failed",
        latency_ms=500,
    )
    response = client.get(
        f"/workspaces/{workspace_id}/usage/model-calls",
        headers=auth_headers(workspace_id, role="viewer"),
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["workspace_id"] == workspace_id
    assert data["total_calls"] == 3
    assert data["success_calls"] == 2
    assert data["failed_calls"] == 1
    assert data["estimated_cost"] == 0
    assert data["average_latency_ms"] == 300
    
def test_get_model_call_usage_summary_forbidden_for_other_workspace()->None:
    workspace_id = create_workspace()
    other_workspace_id = create_workspace()
    
    create_model_call(
        workspace_id=workspace_id,
        status = "success",
        latency_ms=100,
    )
    response = client.get(
        f"/workspaces/{workspace_id}/usage/model-calls",
        headers = auth_headers(other_workspace_id, role="viewer")
    )
    assert response.status_code == 403