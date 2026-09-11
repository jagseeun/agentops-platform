from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.run import Run
from app.repositories.run_repository import RunRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.run import RunCreate, RunStatusUpdate

MAX_RETRY_COUNT = 3

_ALLOWED_TRANSITIONS : dict[str, set[str]]={
    "queued" : {"running", "canceled"},
    "running" : {"completed", "failed"},
    "failed" : {"retry_requested"},
    "retry_requested" : {"queued"},
    "completed" : set(),
    "canceled" : set(),
}

def can_transition(current: str, next_status:str)->bool:
    return next_status in _ALLOWED_TRANSITIONS.get(current, set())

class RunService : 
    def __init__(self,db:Session):
        self.run_repository = RunRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        
    def create_run(self, *, workspace_id: int, workflow_id: int, payload: RunCreate)->Run:
        workflow=self.workflow_repository.get_by_workspace_and_id(
            workspace_id=workspace_id,
            workflow_id=workflow_id,
        )
        if not workflow:
            raise HTTPException(status_code=404, detail="workflow not found")
        if workflow.status != "active":
            raise HTTPException(status_code=409, detail="workflow is not active")
        
        return self.run_repository.create(
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            input_payload=payload.input_payload,
        )
    def get_run(self, *, workspace_id: int, run_id: int)->Run:
        run=self.run_repository.get_by_workspace_and_id(
            workspace_id=workspace_id,
            run_id = run_id,
        )
        if not run:
            raise HTTPException(status_code=404, detail="run not found")
        return run
    def transition_status(self, *, workspace_id:int, run_id:int, payload:RunStatusUpdate)->Run:
        run = self.get_run(workspace_id=workspace_id, run_id = run_id)
        if not can_transition(run.status, payload.status):
            raise HTTPException(
                status_code=422,
                detail=f"cannot transition from {run.status} to {payload.status}",
            )
        return self.run_repository.update_status(run=run, status=payload.status)
    def retry_run(self, *, workspace_id: int, run_id: int)->Run:
        run = self.get_run(workspace_id = workspace_id, run_id = run_id)
        
        if run.status != "failed":
            raise HTTPException(status_code=422, detail = "only failed run can be retried")
        
        if run.retry_count>=MAX_RETRY_COUNT:
            raise HTTPException(status_code=409, detail = "max retry exceeded")
        
        run.retry_count += 1
        run.status = "retry_requested"
        run.status = "queued"
        
        return self.run_repository.save(run)