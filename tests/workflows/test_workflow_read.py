from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def auth_headers(workspace_id: int, role: str = "admin")->dict[str,str]:
    return {
        "X-User-Id": "1",
        "X-Workspace-Id": str(workspace_id),
        "X-User-Role": role,
    }

def unique_slug(prefix: str)->str:
    return f"{prefix}_{uuid4().hex}"

def create_workspace(name:str)->int:
    response = client.post(
        "/workspaces",
        json={"name":name, "slug":unique_slug(name.lower())},
    )
    assert response.status_code==201
    return response.json()["id"]

def create_agent(workspace_id: int, name: str, version:str="v1")->int:
    response = client.post(
        "/agents",
        json={
            "workspace_id": workspace_id,
            "name": name,
            "version": version,
        },
        headers=auth_headers(workspace_id=workspace_id, role="admin"),
    )
    assert response.status_code==201
    return response.json()["id"]

def create_workflow(workspace_id: int, agent_id: int)->int:
    response=client.post(
        f"/workspaces/{workspace_id}/workflows",
        json={
            "name":"document_analysis",
            "steps":[
                {"agent_id":agent_id, "step_order":1},
            ],
        },
        headers=auth_headers(workspace_id=workspace_id, role="admin"),
    )
    assert response.status_code==201
    return response.json()["id"]

def test_get_workflow_returns_steps_with_agent_info()->None:
    workspace_id = create_workspace("Worklfow Read")
    agent_id = create_agent(
        workspace_id= workspace_id,
        name = "summarizer",
        version="v1"
    )
    workflow_id = create_workflow(
        workspace_id=workspace_id,
        agent_id= agent_id,
    )
    response = client.get(
        f"/workspaces/{workspace_id}/workflows/{workflow_id}",
        headers=auth_headers(workspace_id=workspace_id, role="viewer"),
    )
    assert response.status_code==200
    data=response.json()
    assert data["id"]==workflow_id
    assert data["workspace_id"]==workspace_id
    assert data["name"]=="document_analysis"
    assert data["status"]=="draft"
    
    assert len(data["steps"])==1
    step = data["steps"][0]
    assert step["agent_id"] == agent_id
    assert step["agent_name"] == "summarizer"
    assert step["agent_version"] == "v1"
    assert step["step_order"] == 1

def test_get_other_workspace_workflow_return_404()->None:
    workspace_one_id = create_workspace("Workflow Read One")
    workspace_two_id = create_workspace("Workflow Read Two")
    
    agent_id = create_agent(
        workspace_id=workspace_one_id,
        name = "reader-agent",
        version="v1",
    )
    workflow_id = create_workflow(
        workspace_id=workspace_one_id,
        agent_id=agent_id,
    )
    response = client.get(
        f"/workspaces/{workspace_two_id}/workflows/{workflow_id}",
        headers=auth_headers(workspace_id=workspace_two_id, role="viewer"),
    )
    assert response.status_code==404

def test_get_workflow_returns_steps_ordered_by_step_order()->None:
    workspace_id = create_workspace("Workflow Read Order")
    agent_one_id = create_agent(
        workspace_id=workspace_id,
        name="order-agent-one",
        version="v1",
    )
    agent_two_id = create_agent(
        workspace_id=workspace_id,
        name="order-agent-two",
        version="v1",
    )
    workflow_response=client.post(
        f"/workspaces/{workspace_id}/workflows",
        json={
            "name":"ordered_workflow",
            "steps": [
                {"agent_id":agent_one_id, "step_order": 1},
                {"agent_id":agent_two_id, "step_order": 2}
            ],
        },
        headers=auth_headers(workspace_id=workspace_id, role="admin")
    )
    assert workflow_response.status_code==201
    workflow_id = workflow_response.json()["id"]
    
    response = client.get(
        f"/workspaces/{workspace_id}/workflows/{workflow_id}",
        headers=auth_headers(workspace_id=workspace_id, role="viewer")
    )
    assert response.status_code==200
    data=response.json()
    assert [step["step_order"] for step in data["steps"]] == [1,2]
    assert [step["agent_id"] for step in data["steps"]] == [
        agent_one_id,
        agent_two_id,
    ]