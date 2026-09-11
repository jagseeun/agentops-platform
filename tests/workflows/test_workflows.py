from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def auth_headers(workspace_id:int, role:str="admin")->dict[str,str]:
    return {
        "X-User-Id":"1",
        "X-Workspace-Id":str(workspace_id),
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

def create_agent(workspace_id: int, name: str, version: str = "1.0.0")-> int:
    response = client.post(
        "/agents",
        json={
            "workspace_id":workspace_id,
            "name":name,
            "version": version,
        },
        headers=auth_headers(workspace_id=workspace_id, role="admin"),
    )
    assert response.status_code==201
    return response.json()["id"]

def create_workflow_response(*, workspace_id:int, agent_ids: list[int], role: str = "admin", step_orders:list[int] | None=None,):
    orders=step_orders or list(range(1, len(agent_ids)+1))
    
    return client.post(
        f"/workspaces/{workspace_id}/workflows",
        json={
            "name":"document_analysis",
            "steps":[
                {"agent_id":agent_id,"step_order":step_order}
                for agent_id, step_order in zip(agent_ids, orders, strict=True)
                
            ],
        },
        headers=auth_headers(workspace_id=workspace_id, role=role),
    )

def test_admin_can_create_workflow()->None:
    workspace_id = create_workspace("Workflow Admin")
    agent_one_id =create_agent(workspace_id, "workflow-agent-one")
    agent_two_id = create_agent(workspace_id, "workflow-agent-two")
    
    response = create_workflow_response(
        workspace_id = workspace_id,
        agent_ids = [agent_one_id, agent_two_id],
        role="admin",
    )
    assert response.status_code==201
    data=response.json()
    assert data["workspace_id"] == workspace_id
    assert data["name"] == "document_analysis"
    assert data["status"] == "draft"
    
def test_developer_can_create_workflow()->None:
    workspace_id = create_workspace("Workflow Developer")
    agent_id = create_agent(workspace_id, "workflow-developer-agent")
    response = create_workflow_response(
        workspace_id = workspace_id,
        agent_ids = [agent_id],
        role="developer",
    )
    assert response.status_code==201

def test_viewer_cannot_create_workflow()->None:
    workspace_id = create_workspace("Workflow Viewer")
    agent_id = create_agent(workspace_id, "workspace_viewer-agent")
    
    response = create_workflow_response(
        workspace_id=workspace_id,
        agent_ids=[agent_id],
        role="viewer",
    )
    assert response.status_code==403

def test_workflow_step_order_must_start_from_one()->None:
    workspace_id = create_workspace("Workflow Step Start")
    agent_id = create_agent(workspace_id, "workflow-step-agent")
    response = create_workflow_response(
        workspace_id=workspace_id,
        agent_ids=[agent_id],
        step_orders=[2],
    )
    assert response.status_code == 422
    
def test_workflow_step_order_cannot_be_duplicated()->None:
    workspace_id = create_workspace("Workflow Duplicate Step")
    agent_one_id = create_agent(workspace_id, "workflow-duplicate-agent-one")
    agent_two_id = create_agent(workspace_id, "workflow-duplicate-agent-two")
    
    response = create_workflow_response(
        workspace_id = workspace_id,
        agent_ids=[agent_one_id, agent_two_id],
        step_orders=[1,1],
    )    
    assert response.status_code == 422
    
def test_workflow_cannot_use_other_workspace_agent()->None:
    workspace_one_id = create_workspace("Workflow Tenant One")
    workspace_two_id = create_workspace("Workflow Tenant Two")
    
    other_workspace_agent_id = create_agent(
        workspace_two_id,
        "workflow-other-workspace-agent",
    )
    response = create_workflow_response(
        workspace_id = workspace_one_id,
        agent_ids = [other_workspace_agent_id],
    )
    assert response.status_code == 404
    
    
def test_workflow_cannot_use_inactive_agent()->None:
    workspace_id = create_workspace("Workflow Inactive")
    agent_id = create_agent(workspace_id, "workflow-inactive-agent")
    
    deactivate_response = client.post(
        f"/workspaces/{workspace_id}/agents/{agent_id}/deactivate",
        headers = auth_headers(workspace_id = workspace_id, role = "admin"),
        
    )
    assert deactivate_response.status_code==200
    
    response = create_workflow_response(
        workspace_id =workspace_id,
        agent_ids = [agent_id],
    )
    assert response.status_code == 409