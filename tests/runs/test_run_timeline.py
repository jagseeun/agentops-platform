from uuid import uuid4

from fastapi.testclient import TestClient
from app.db.session import SessionLocal
from app.main import app
from app.models.workflow import Workflow
from app.repositories.run_event_repository import RunEventRepository

client = TestClient(app)

def auth_headers(workspace_id: int, role: str = "admin")->dict[str,str]:
    return {
        "X-User-Id" : "1",
        "X-Workspace-Id" : str(workspace_id),
        "X-User-Role" : role,
    }

def unique_slug(prefix : str) -> str:
    return f"{prefix}_{uuid4().hex}"

def create_workspace(name: str)->int:
    response = client.post(
        "/workspaces",
        json={"name": name, "slug":unique_slug(name.lower())},
    )
    assert response.status_code == 201
    return response.json()["id"]

def create_agent(workspace_id: int, name: str) -> int:
    response=client.post(
        "/agents",
        json = {
            "workspace_id" : workspace_id,
            "name" : name,
            "version": "1.0.0"
        },
        headers=auth_headers(workspace_id=workspace_id, role="admin")
    )
    assert response.status_code == 201
    return response.json()["id"]

def activate_workflow(workflow_id: int)->None:
    db = SessionLocal()
    try:
        workflow = db.get(Workflow, workflow_id)
        assert workflow is not None
        workflow.status = "active"
        db.commit()
    finally:
        db.close()
        
def create_workflow(workspace_id: int, agent_id : int)->int:
    response = client.post(
        f"/workspaces/{workspace_id}/workflows",
        json={
            "name": "timeline_workflow",
            "steps" : [
                {"agent_id": agent_id, "step_order": 1},
            ],
        },
        headers = auth_headers(workspace_id = workspace_id, role="admin"),
    )
    assert response.status_code == 201
    workflow_id = response.json()["id"]
    activate_workflow(workflow_id)
    return workflow_id

def create_run(workspace_id: int, workflow_id : int)->int:
    response =client.post(
        f"/workspaces/{workspace_id}/workflows/{workflow_id}/runs",
        json={},
        headers = auth_headers(workspace_id=workspace_id, role="admin"),
    )
    assert response.status_code == 201
    return response.json()["id"]

def create_run_event(
    *, workspace_id: int, run_id: int, event_type:str, message: str
)->None:
    db = SessionLocal()
    try:
        repository = RunEventRepository(db)
        repository.create(
            workspace_id = workspace_id,
            run_id = run_id,
            event_type = event_type,
            message = message,
        )
    finally:
        db.close()
        
def test_get_run_timeline_returns_events_in_order()->None:
    workspace_id = create_workspace("Timeline Workspace")
    agent_id = create_agent(workspace_id, "timeline-agent")
    workflow_id = create_workflow(workspace_id, agent_id)
    run_id = create_run(workspace_id, workflow_id)
    
    create_run_event(
        workspace_id = workspace_id,
        run_id = run_id,
        event_type="run_started",
        message = "Run started"
    )
    create_run_event(
        workspace_id = workspace_id,
        run_id = run_id,
        event_type = "step_started",
        message= "Step 1 started",
    )
    response = client.get(
        f"/workspaces/{workspace_id}/runs/{run_id}/timeline",
        headers=auth_headers(workspace_id= workspace_id, role="viewer"),
    )
    assert response.status_code == 200
    data =response.json()
    assert data["run_id"] == run_id
    assert [event["event_type"] for event in data["events"]] == [
        "run_started",
        "step_started",
    ]
def test_get_other_workspace_run_timeline_returns_404()->None:
    ws1 = create_workspace("Timeline One")
    ws2 = create_workspace("Timeline Two")
    
    agent_id = create_agent(ws1, "timieline-other-agent")
    workflow_id = create_workflow(ws1, agent_id)
    run_id = create_run(ws1, workflow_id)
    
    response = client.get(
        f"/workspaces/{ws2}/runs/{run_id}/timeline",
        headers = auth_headers(workspace_id=ws2, role="viewer"),
    )
    assert response.status_code == 404
    