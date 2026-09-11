from uuid import uuid4
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.run import Run
from app.models.workflow import Workflow
from app.workers.run_worker import (
    fail_timed_out_runs,
    process_next_queued_run,
    process_run
)
from app.models.model_call import ModelCall

client = TestClient(app)

def clear_queued_runs()->None:
    db = SessionLocal()
    try:
        db.query(Run).filter(Run.status == "queued").update(
            {"status" : "completed"}
        )
        db.commit()
    finally:
        db.close()

def set_run_running_started_at(run_id: int, started_at: datetime)->None:
    db = SessionLocal()
    try:
        run =db.get(Run, run_id)
        assert run is not None
        run.status = "running"
        run.started_at = started_at
        db.commit()
    finally:
        db.close()

def test_process_next_queued_run_completes_oldest_queued_run() -> None:
    clear_queued_runs()
    workspace_id = create_workspace("Polling Worker")
    agent_id = create_agent(workspace_id, "polling-worker-agent")
    workflow_id = create_workflow(workspace_id, agent_id)
    run_id = create_run(workspace_id, workflow_id)
    
    processed = process_next_queued_run()
    
    db = SessionLocal()
    try : 
        run = db.get(Run, run_id)
        
        assert processed is True
        assert run is not None
        assert run.status == "completed"
    finally:
        db.close()

def auth_headers(workspace_id: int, role: str = "admin") -> dict[str, str]:
    return {
        "X-User-Id" : "1",
        "X-Workspace-Id" : str(workspace_id),
        "X-User-Role": role,
    }

def unique_slug(prefix : str) -> str:
    return f"{prefix}_{uuid4().hex}"

def create_workspace(name: str)->int:
    response = client.post(
        "/workspaces",
        json={"name":name,"slug":unique_slug(name.lower())},
    )
    assert response.status_code == 201
    return response.json()["id"]

def create_agent(workspace_id : int, name: str, version: str = "1.0.0")->int:
    response = client.post(
        "/agents",
        json ={
            "workspace_id" : workspace_id,
            "name": name,
            "version" : version,
        },
        headers=auth_headers(workspace_id=workspace_id, role="admin"),
    )
    assert response.status_code == 201
    return response.json()["id"]

def activate_workflow(workflow_id:int)->None:
    db=SessionLocal()
    try:
        workflow=db.get(Workflow,workflow_id)
        assert workflow is not None
        workflow.status = "active"
        db.commit()
    finally:
        db.close()
        
def create_workflow(workspace_id: int, agent_id: int, input_mapping: str | None = None)->int:
    response = client.post(
        f"/workspaces/{workspace_id}/workflows",
        json={
            "name":"worker_workflow",
            "steps":[
                {"agent_id" : agent_id, "step_order" : 1, "input_mapping": input_mapping},
            ],
        },
        headers = auth_headers(workspace_id=workspace_id, role = "admin"),
    )
    assert response.status_code == 201
    workflow_id = response.json()["id"]
    activate_workflow(workflow_id)
    return workflow_id

def create_run(workspace_id : int, workflow_id : int)->int:
    response = client.post(
        f"/workspaces/{workspace_id}/workflows/{workflow_id}/runs",
        json={},
        headers=auth_headers(workspace_id=workspace_id, role="admin"),
    )
    assert response.status_code == 201
    return response.json()["id"]

def test_process_run_completes_queued_run()->None:
    workspace_id = create_workspace("Worker Success")
    agent_id = create_agent(workspace_id, "worker-agent")
    workflow_id = create_workflow(workspace_id, agent_id)
    run_id = create_run(workspace_id, workflow_id)
    
    process_run(run_id)
    
    db = SessionLocal()
    
    try:
        run =db.get(Run, run_id)
        assert run is not None
        assert run.status == "completed"
        assert run.started_at is not None
        assert run.finished_at is not None
        assert run.error_message is None
    finally:
        db.close()

def test_process_run_marks_failed_when_step_fails(monkeypatch)->None:
    workspace_id = create_workspace("Worker Failure")
    agent_id = create_agent(workspace_id, "worker-fail-agent")
    workflow_id = create_workflow(workspace_id, agent_id)
    run_id = create_run(workspace_id, workflow_id)
    
    def fail_step(*, db, run, step)->None:
        raise RuntimeError("step failed")
    
    monkeypatch.setattr(
        "app.workers.run_worker._process_step",
        fail_step,
    )
    
    process_run(run_id)
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        assert run is not None
        assert run.status == "failed"
        assert run.error_message == "step failed"
        assert run.started_at is not None
        assert run.finished_at is not None
    finally:
        db.close()

def test_fail_timed_out_runs_marks_old_running_run_failed() -> None:
    workspace_id = create_workspace("Multiple Timeout Run")
    agent_id = create_agent(workspace_id, "multiple-timeout-agent")
    workflow_id = create_workflow(workspace_id, agent_id)
    
    first_run_id = create_run(workspace_id, workflow_id)
    second_run_id = create_run(workspace_id, workflow_id)
    
    old_time = datetime.now() - timedelta(seconds=120)
    
    set_run_running_started_at(first_run_id, old_time)
    set_run_running_started_at(second_run_id, old_time)
    
    failed_count = fail_timed_out_runs(timeout_seconds=60)
    
    db = SessionLocal()
    try:
        first_run = db.get(Run, first_run_id)
        second_run = db.get(Run, second_run_id)
        
        assert failed_count >= 2
        assert first_run is not None
        assert second_run is not None
        assert first_run.status == "failed"
        assert second_run.status == "failed"
    finally:
        db.close()

def test_timed_out_run_can_be_retried() -> None:
    workspace_id = create_workspace("Timeout Retry")
    agent_id = create_agent(workspace_id, "timeout-retry-agent")
    workflow_id = create_workflow(workspace_id, agent_id)
    run_id = create_run(workspace_id, workflow_id)
    
    set_run_running_started_at(
        run_id = run_id,
        started_at = datetime.now()-timedelta(seconds=120),
    )
    fail_timed_out_runs(timeout_seconds=60)
    
    response = client.post(
        f"/workspaces/{workspace_id}/runs/{run_id}/retry",
        headers = auth_headers(workspace_id=workspace_id, role ="admin"),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert response.json()["retry_count"] == 1
    assert response.json()["error_message"] == "run timed out after 60 seconds"
    
    
def test_process_run_records_model_call_for_step()->None:
    workspace_id = create_workspace("Worker Model Gateway")
    agent_id = create_agent(workspace_id, "worker-model-agent")
    workflow_id = create_workflow(workspace_id, agent_id)
    run_id = create_run(workspace_id, workflow_id)
    
    process_run(run_id)
    db = SessionLocal()
    try : 
        model_call = (
            db.query(ModelCall)
            .filter(
                ModelCall.workspace_id == workspace_id,
                ModelCall.run_id == run_id,
            )
            .order_by(ModelCall.id.desc())
            .first()
        )
        assert model_call is not None
        assert model_call.provider == "fake"
        assert model_call.model_name == "fake-model"
        assert model_call.status == "success"
        assert model_call.error_message is None
        assert model_call.latency_ms >= 0
    finally:
        db.close()
        
def test_failed_provider_run_can_be_explained_from_timeline()->None:
    workspace_id = create_workspace("Provider Failure Timeline")
    agent_id = create_agent(workspace_id, "provider-failure-agent")
    workflow_id = create_workflow(
        workspace_id,
        agent_id,
        input_mapping="please FAIL",
    )
    run_id = create_run(workspace_id, workflow_id)
    process_run(run_id)
    
    response = client.get(
        f"/workspaces/{workspace_id}/runs/{run_id}/timeline",
        headers = auth_headers(workspace_id= workspace_id, role="viewer"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == run_id
    assert [event["event_type"] for event in data["events"]]==[
        "run_started",
        "step_started",
        "model_call_failed",
        "run_failed",
    ]
    assert data["events"][2]["message"] == "fake provider failure"