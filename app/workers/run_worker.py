from app.db.session import SessionLocal
from app.models.run import Run
from sqlalchemy.orm import Session
from app.services.model_gateway import ModelGateway
from app.models.workflow_step import WorkflowStep

from app.repositories.run_event_repository import RunEventRepository
from datetime import datetime, timedelta

def process_next_queued_run()->bool:
    db = SessionLocal()
    try:
        run = (
            db.query(Run)
            .filter(Run.status == "queued")
            .order_by(Run.created_at)
            .first()
        )
        if run is None:
            return False
        run_id = run.id
    finally:
        db.close()
    process_run(run_id)
    return True

def process_run(run_id : int)-> None:
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        if run is None:
            return
        if run.status != "queued":
            return
        
        event_repository = RunEventRepository(db)
        
        run.status = "running"
        run.started_at = datetime.now()
        db.commit()
        db.refresh(run)
        
        event_repository.create(
            workspace_id = run.workspace_id,
            run_id = run.id,
            event_type = "run_started",
            message = "Run started",
        )
        
        steps = (
            db.query(WorkflowStep)
            .filter(WorkflowStep.workflow_id == run.workflow_id)
            .order_by(WorkflowStep.step_order)
            .all()
        )
        try:
            for step in steps:
                event_repository.create(
                    workspace_id=run.workspace_id,
                    run_id=run.id,
                    event_type="step_started",
                    message = f"Step {step.step_order} started",
                    event_metadata={
                        "step_id" : step.id,
                        "agent_id": step.agent_id
                    }
                )
                _process_step(db=db, run=run, step=step)
            run.status = "completed"
            run.finished_at = datetime.now()
            db.commit()
            db.refresh(run)
            event_repository.create(
                workspace_id = run.workspace_id,
                run_id = run.id,
                event_type="run_completed",
                message = "Run completed"
            )
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            run.finished_at = datetime.now()
            db.commit()
            db.refresh(run)
            
            event_repository.create(
                workspace_id = run.workspace_id,
                run_id = run.id,
                event_type = "run_failed",
                message= "Run failed",
                event_metadata={
                    "error_message" : str(exc),
                },
            )
    finally:
        db.close()
        
        
def _process_step(*, db:Session, run: Run, step: WorkflowStep)->None:
    gateway = ModelGateway(db)
    event_repository = RunEventRepository(db)
    prompt = step.input_mapping or f"Process workflow step {step.id}"
    try:
        gateway.complete(
            workspace_id=run.workspace_id,
            run_id = run.id,
            prompt=prompt,
        )
    except Exception as exc : 
        event_repository.create(
            workspace_id = run.workspace_id,
            run_id = run.id,
            event_type = "model_call_failed",
            message = str(exc),
            event_metadata={
                "step_id" : step.id,
                "agent_id" : step.agent_id,
            },
        )
        raise
    
def fail_timed_out_runs(timeout_seconds: int)->int:
    cutoff = datetime.now() - timedelta(seconds=timeout_seconds)
    db = SessionLocal()
    try:
        runs = (
            db.query(Run)
            .filter(
                Run.status=="running",
                Run.started_at < cutoff,
            )
            .all()
        )
        for run in runs:
            run.status = "failed"
            run.error_message = f"run timed out after {timeout_seconds} seconds"
            run.finished_at = datetime.now()
            
        db.commit()
        return len(runs)
        
    finally:
        db.close()