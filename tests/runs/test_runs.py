from uuid import uuid4
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.workflow import Workflow
from app.models.run import Run

client = TestClient(app)

def auth_headers(workspace_id: int, role: str = "admin")->dict[str,str]:
    return {
        "X-User-Id": "1",
        "X-Workspace-Id" : str(workspace_id),
        "X-User-Role" : role,
    } 

def unique_slug(prefix: str)->str:
    return f"{prefix}_{uuid4().hex}"

def create_workspace(name:str)->int:
    response = client.post(
        "/workspaces",
        json={"name":name, "slug":unique_slug(name.lower())},
    )
    assert response.status_code == 201
    return response.json()["id"]

def create_agent(workspace_id: int, name: str, version: str = "1.0.0")-> int:
    response = client.post(
        "/agents",
        json={
            "workspace_id" : workspace_id,
            "name": name,
            "version" : version,
        },
        headers=auth_headers(workspace_id=workspace_id,role="admin"),
    )
    assert response.status_code == 201
    return response.json()["id"]

def create_workflow(workspace_id: int, agent_id: int)->int:
    response =client.post(
        f"/workspaces/{workspace_id}/workflows",
        json={
            "name":"test_workflow",
            "steps":[
                {"agent_id": agent_id, "step_order":1},
            ],
        },
        headers=auth_headers(workspace_id=workspace_id, role="admin"),
    )
    assert response.status_code == 201
    workflow_id = response.json()["id"]
    activate_workflow(workflow_id)
    
    return workflow_id

def activate_workflow(workflow_id: int) -> None:
    db = SessionLocal()
    try: 
        workflow= db.get(Workflow, workflow_id)
        assert workflow is not None
        workflow.status = "active"
        db.commit()
    finally:
        db.close()

def create_run(workspace_id: int, workflow_id: int, role: str="admin"):
    return client.post(
        f"/workspaces/{workspace_id}/workflows/{workflow_id}/runs",
        json={},
        headers=auth_headers(workspace_id=workspace_id, role=role),
    )

def set_run_retry_count(run_id: int, retry_count: int)->None:
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        assert run is not None
        run.retry_count = retry_count
        db.commit()
    finally:
        db.close()

class TestCreateRun:
    def test_admin_can_create_run(self)->None:
        workspace_id = create_workspace("Run Admin")
        agent_id = create_agent(workspace_id, "run-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        response = create_run(workspace_id, workflow_id, role="admin")
        assert response.status_code == 201
        data = response.json()
        assert data["workflow_id"] == workflow_id
        assert data["workspace_id"] == workspace_id
        assert data["status"] == "queued"
        
    def test_developer_can_create_run(self)->None:
        workspace_id = create_workspace("Run Developer")
        agent_id = create_agent(workspace_id, "run-dev-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        response = create_run(workspace_id, workflow_id, role="developer")
        assert response.status_code == 201
        
    def test_viewer_cannot_create_run(self) -> None:
        workspace_id = create_workspace("Run Viewer")
        agent_id = create_agent(workspace_id, "run-viewer-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        
        response = create_run(workspace_id, workflow_id, role="viewer")
        assert response.status_code == 403
        
    def test_create_run_nonexistent_workflow(self)->None:
        workspace_id = create_workspace("Run No Workflow")
        
        response = client.post(
            f"/workspaces/{workspace_id}/workflows/99999/runs",
            json={},
            headers=auth_headers(workspace_id=workspace_id, role="admin"),
        )
        assert response.status_code==404
    def test_create_run_enqueues_process_run_task_after_commit(self, monkeypatch)->None:
        workspace_id = create_workspace("Run Enqueue")
        agent_id = create_agent(workspace_id, "run-enqueue-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        enqueued_run_ids = []
        
        def fake_delay(run_id:int)->None:
            db = SessionLocal()
            try:
                run=db.get(Run, run_id)
                assert run is not None
                assert run.status == "queued"
            finally: 
                db.close()
            enqueued_run_ids.append(run_id)
        monkeypatch.setattr(
            "app.api.routes.runs.process_run_task.delay",
            fake_delay,
        )
        response = create_run(workspace_id, workflow_id, role="admin")
        
        assert response.status_code == 201
        assert enqueued_run_ids == [response.json()["id"]]
        
class TestGetRun:
    def test_get_run_returns_data(self)->None:
        workspace_id = create_workspace("Run Get")
        agent_id = create_agent(workspace_id, "run-get-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        
        create_resp = create_run(workspace_id, workflow_id)
        run_id = create_resp.json()["id"]
        
        response = client.get(
            f"/workspaces/{workspace_id}/runs/{run_id}",
            headers=auth_headers(workspace_id=workspace_id, role="viewer"),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
        assert data["workflow_id"] == workflow_id
        assert data["workspace_id"] == workspace_id
        assert data["status"] == "queued"
        
    def test_get_other_workspace_run_404(self)->None:
        ws1 = create_workspace("Run Other One")
        ws2 = create_workspace("Run Other Two")
            
        agent_id = create_agent(ws1, "run-other-agent")
        workflow_id = create_workflow(ws1, agent_id)
            
        create_resp = create_run(ws1, workflow_id)
        run_id = create_resp.json()["id"]
            
        response = client.get(
            f"/workspaces/{ws2}/runs/{run_id}",
            headers=auth_headers(workspace_id=ws2, role="viewer"),
        )
        assert response.status_code == 404
        
class TestStateTransitions:
    def test_valid_queued_to_running_to_completed(self) -> None:
        workspace_id = create_workspace("Run Transition")
        agent_id = create_agent(workspace_id, "transition-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        
        create_resp = create_run(workspace_id, workflow_id)
        run_id = create_resp.json()["id"]
        
        resp1 = client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status": "running"},
            headers=auth_headers(workspace_id=workspace_id, role="admin"),
        )
        assert resp1.status_code==200
        assert resp1.json()["status"]=="running"
        
        resp2 = client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status":"completed"},
            headers = auth_headers(workspace_id=workspace_id, role="admin"),
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "completed"
    
    def test_valid_queued_to_canceled(self)->None:
        workspace_id = create_workspace("Run Cancel")
        agent_id = create_agent(workspace_id, "cancel-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        
        create_resp = create_run(workspace_id, workflow_id)
        run_id = create_resp.json()["id"]
        
        response = client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status":"canceled"},
            headers=auth_headers(workspace_id=workspace_id, role="admin"),
        )
        assert response.status_code==200
        assert response.json()["status"] == "canceled"
    
    def test_invalid_queued_to_completed(self) -> None:
        workspace_id = create_workspace("Run Invalid")
        agent_id = create_agent(workspace_id, "invalid-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        
        create_resp = create_run(workspace_id, workflow_id)
        run_id = create_resp.json()["id"]
        
        response = client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status":"completed"},
            headers=auth_headers(workspace_id=workspace_id, role="admin"),
        )
        assert response.status_code == 422
        
    def test_invalid_failed_to_completed(self)->None:
        workspace_id = create_workspace("Run Failed Complete")
        agent_id = create_agent(workspace_id, "failed-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        
        create_resp = create_run(workspace_id, workflow_id)
        run_id = create_resp.json()["id"]
        
        client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status": "running"},
            headers=auth_headers(workspace_id=workspace_id, role="admin"),
        )
        client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status":"failed"},
            headers=auth_headers(workspace_id=workspace_id, role="admin"),
        )
        response = client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status":"completed"},
            headers=auth_headers(workspace_id=workspace_id, role="admin"),
        )
        assert response.status_code == 422
        
    def test_invalid_canceled_to_running(self)->None:
        workspace_id = create_workspace("Run Canceled Run")
        agent_id = create_agent(workspace_id, "canceled-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        
        create_resp = create_run(workspace_id, workflow_id)
        run_id = create_resp.json()["id"]
        
        client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status":"canceled"},
            headers=auth_headers(workspace_id=workspace_id, role="admin"),
        )
        response = client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status": "running"},
            headers = auth_headers(workspace_id=workspace_id, role="admin"),
        )
        assert response.status_code==422
    def test_valid_running_to_failed(self)->None:
        workspace_id = create_workspace("Run Running Failed")
        agent_id = create_agent(workspace_id, "running-failed-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        
        create_resp = create_run(workspace_id, workflow_id)
        run_id = create_resp.json()["id"]
        
        client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status" : "running"},
            headers=auth_headers(workspace_id = workspace_id, role="admin"),
        )
        
        response = client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status" : "failed"},
            headers = auth_headers(workspace_id=workspace_id, role="admin"),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "failed"
        
        def test_invalid_completed_to_running(self) -> None:
            workspace_id = create_workspace("Run Completed Running")
            agent_id = create_agent(workspace_id, "completed-running-agent")
            workflow_id = create_workflow(workspace_id, agent_id)
            
            create_resp = create_run(workspace_id, workflow_id)
            run_id = create_resp.json()["id"]
            
            client.patch(
                f"/workspaces/{workspace_id}/runs/{run_id}/status",
                json = {"status" : "running"},
                headers = auth_headers(workspace_id= workspace_id, role="admin"),
            )
            client.patch(
                f"/workspaces/{workspace_id}/runs/{run_id}/status",
                json = {"status" : "completed"},
                headers=auth_headers(workspace_id=workspace_id, role = "admin"),
            )
            
            response = client.patch(
                f"/workspaces/{workspace_id}/runs/{run_id}/status",
                json = {"status" : "running"},
                headers = auth_headers(workspace_id=workspace_id,role="admin"),
            )
            assert response.status_code == 422
            
class Test_RetryRun:
    def test_failed_run_can_be_retried(self) -> None:
        workspace_id = create_workspace("Run Retry Failed")
        agent_id = create_agent(workspace_id, "retry-failed-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        
        create_resp = create_run(workspace_id,workflow_id)
        run_id = create_resp.json()["id"]
        
        client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json = {"status" : "running"},
            headers = auth_headers(workspace_id=workspace_id, role = "admin")
        )
        client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status":"failed"},
            headers=auth_headers(workspace_id=workspace_id, role = "admin"),
        )
        response=client.post(
            f"/workspaces/{workspace_id}/runs/{run_id}/retry",
            headers=auth_headers(workspace_id=workspace_id, role = "admin")
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "queued"
        assert response.json()["retry_count"] == 1
        
    def test_completed_run_cannot_be_retried(self) -> None:
        workspace_id = create_workspace("Run Retry Completed")
        agent_id = create_agent(workspace_id, "retry-completed-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        
        create_resp = create_run(workspace_id, workflow_id)
        run_id = create_resp.json()["id"]
        
        client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json = {"status": "running"},
            headers=auth_headers(workspace_id=workspace_id, role="admin"),
        )
        client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status":"completed"},
            headers = auth_headers(workspace_id=workspace_id, role="admin")
        )
        
        response = client.post(
            f"/workspaces/{workspace_id}/runs/{run_id}/retry",
            headers=auth_headers(workspace_id = workspace_id, role = "admin")
        )
        
        assert response.status_code == 422
    def test_retry_fails_when_max_retry_exceeded(self)->None:
        workspace_id = create_workspace("Run Retry Max")
        agent_id = create_agent(workspace_id, "retry_max_agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        
        create_resp = create_run(workspace_id, workflow_id)
        run_id = create_resp.json()["id"]
        
        client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json = {"status" : "running"},
            headers = auth_headers(workspace_id=workspace_id, role = "admin"),
        )
        
        client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json = {"status":"failed"},
            headers=auth_headers(workspace_id=workspace_id, role = "admin"),
        )
        set_run_retry_count(run_id, 3)
        response =client.post(
            f"/workspaces/{workspace_id}/runs/{run_id}/retry",
            headers = auth_headers(workspace_id=workspace_id, role = "admin")
        )
        assert response.status_code == 409
        
    def test_viewer_cannot_retry_run(self)->None:
        workspace_id = create_workspace("Retry Viewer")
        agent_id = create_agent(workspace_id, "retry-viewer-agent")
        workflow_id = create_workflow(workspace_id, agent_id)
        
        create_resp = create_run(workspace_id, workflow_id)
        run_id = create_resp.json()["id"]
        
        client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status":"running"},
            headers=auth_headers(workspace_id=workspace_id, role="admin"),
        )
        client.patch(
            f"/workspaces/{workspace_id}/runs/{run_id}/status",
            json={"status":"failed"},
            headers=auth_headers(workspace_id=workspace_id, role="admin"),
        )
        response = client.post (
            f"/workspaces/{workspace_id}/runs/{run_id}/retry",
            headers = auth_headers(workspace_id= workspace_id, role="viewer"),
        )
        assert response.status_code == 403