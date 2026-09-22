from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import UserContext
from app.db.session import get_db
from app.models.run import Run
from app.schemas.run import RunCreate, RunRead, RunStatusUpdate
from app.services.run_service import RunService

from app.schemas.run_event import RunTimelineRead
from app.services.run_event_service import RunEventService

from app.repositories.audit_log_repository import AuditLogRepository

from app.workers.tasks import process_run_task

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["runs"])

@router.post("/workflows/{workflow_id}/runs", response_model=RunRead, status_code = status.HTTP_201_CREATED,)
def create_run(
    workspace_id: int,
    workflow_id : int,
    payload: RunCreate,
    db: Session = Depends(get_db),
    current_user : UserContext = Depends(require_roles(["admin", "developer"])),
)-> Run : 
    if workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="workspace forbidden")
    
    service = RunService(db)
    run =service.create_run(
        workspace_id = workspace_id,
        workflow_id = workflow_id,
        payload = payload,
    )
    AuditLogRepository(db).create(
        workspace_id=workspace_id,
        actor_user_id=current_user.user_id,
        action = "create_run",
        resource_type="Run",
        resource_id = run.id,
        audit_metadata={
            "workflow_id":workflow_id,
            "status":run.status,
        },
    )
    process_run_task.delay(run.id)
    return run

@router.get("/runs/{run_id}", response_model=RunRead)
def get_run(
    workspace_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_roles(["admin", "developer","viewer"])),
)->Run:
    if workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="workspace forbidden")
    
    service = RunService(db)
    return service.get_run(workspace_id=workspace_id, run_id=run_id)

@router.patch("/runs/{run_id}/status", response_model=RunRead)
def update_run_status(
    workspace_id : int,
    run_id: int,
    payload : RunStatusUpdate,
    db:Session = Depends(get_db),
    current_user: UserContext = Depends(require_roles(["admin", "developer"])),
)->Run:
    if workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="workspace forbidden")
    service = RunService(db)
    return service.transition_status(
        workspace_id=workspace_id,
        run_id=run_id,
        payload=payload
    )

@router.post("/runs/{run_id}/retry", response_model = RunRead)
def retry_run(
    workspace_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_roles(["admin", "developer"]))
)->Run:
    if workspace_id != current_user.workspace_id:
        raise HTTPException(status_code = 403, detail="workspace forbidden")
    
    service = RunService(db)
    run = service.retry_run(
        workspace_id = workspace_id,
        run_id = run_id,
    )
    
    AuditLogRepository(db).create(
        workspace_id = workspace_id,
        actor_user_id = current_user.user_id,
        action = "retry_run",
        resource_type="Run",
        resource_id=run.id,
        audit_metadata={
            "status" : run.status,
            "retry_count" : run.retry_count,
        } 
    )
    return run
    

@router.get("/runs/{run_id}/timeline", response_model=RunTimelineRead)
def get_run_timeline(
    workspace_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user : UserContext = Depends (require_roles(["admin", "developer","viewer"])),     
)->RunTimelineRead:
    if workspace_id != current_user.workspace_id:
        raise HTTPException(status_code= 403, detail="workspace forbidden")
    service = RunEventService(db)
    return service.get_timeline(workspace_id=workspace_id, run_id=run_id)
