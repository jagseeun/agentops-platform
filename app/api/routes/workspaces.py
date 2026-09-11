from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.schemas.agent import AgentRead
from app.services.agent_service import AgentService
from app.db.session import get_db
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceRead
from app.services.workspace_service import WorkspaceService

from app.api.deps import require_roles
from app.core.security import UserContext

from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowDetailRead, WorkflowRead
from app.services.workflow_service import WorkflowService

from app.models.data_source import DataSource
from app.schemas.data_source import DataSourceCreate, DataSourceRead
from app.services.data_source_service import DataSourceService

from app.schemas.model_usage import ModelUsageSummaryRead
from app.services.model_usage_service import ModelUsageService

from app.repositories.audit_log_repository import AuditLogRepository

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(payload: WorkspaceCreate, db: Session=Depends(get_db))-> Workspace:
    service = WorkspaceService(db)
    return service.create_workspace(payload)

@router.get("/{workspace_id}/agents", response_model=list[AgentRead])
def list_agents(
    workspace_id: int,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user : UserContext = Depends(require_roles(["admin", "developer", "viewer"])),
)->list[Agent]:
    if workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="workspace forbidden")
    if status is not None and status not in {"active", "inactive"}:
        raise HTTPException(status_code=422, detail="invalid status")
    service = AgentService(db)
    return service.list_agents(workspace_id=workspace_id, status=status)

@router.post("/{workspace_id}/agents/{agent_id}/deactivate", response_model=AgentRead)
def deactivate_agent(
    workspace_id:int,
    agent_id : int,
    db:Session=Depends(get_db),
    current_user: UserContext = Depends(require_roles(["admin"])),
    )->Agent:
    if workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail = "workspace forbidden")
    service=AgentService(db)
    agent = service.deactivate_agent(
        workspace_id = workspace_id,
        agent_id = agent_id,
    )
    
    AuditLogRepository(db).create(
        workspace_id = workspace_id,
        actor_user_id = current_user.user_id,
        action = "deactivate_agent",
        resource_type = "Agent", 
        resource_id = agent.id,
        audit_metadata={
            "status" : agent.status
        }
    )
    return agent
    
@router.post(
    "/{workspace_id}/workflows",
    response_model=WorkflowRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow(
    workspace_id : int,
    payload : WorkflowCreate,
    db : Session = Depends(get_db),
    current_user: UserContext = Depends(require_roles(["admin", "developer"])),
)->Workflow:
    if workspace_id!=current_user.workspace_id:
        raise HTTPException(status_code=403, detail="workspace forbidden")
    
    service = WorkflowService(db)
    
    workflow = service.create_workflow(
        workspace_id = workspace_id,
        payload = payload,
    )
    AuditLogRepository(db).create(
        workspace_id = workspace_id,
        actor_user_id = current_user.user_id,
        action="create_workflow",
        resource_type="Workflow",
        resource_id = workflow.id,
        audit_metadata = {
            "name":workflow.name,
            "status" : workflow.status,
        },
    )
    return workflow


@router.get(
    "/{workspace_id}/workflows/{workflow_id}",
    response_model = WorkflowDetailRead,
)
def get_workflow(workspace_id: int, workflow_id: int, db: Session=Depends(get_db), current_user: UserContext=Depends(require_roles(["admin", "developer", "viewer"])),)->WorkflowDetailRead:
    if workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="workspace forbidden")
    service = WorkflowService(db)
    return service.get_workflow(
        workspace_id=workspace_id,
        workflow_id=workflow_id,
    )
    
@router.post(
    "/{workspace_id}/data-sources",
    response_model = DataSourceRead,
    status_code = status.HTTP_201_CREATED,
)
def create_data_source(
    workspace_id : int,
    payload: DataSourceCreate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_roles(["admin", "developer"])),
)->DataSource:
    if workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="workspace forbidden")
    
    service = DataSourceService(db)
    return service.create_data_source(
        workspace_id = workspace_id,
        payload = payload,
    )
    
@router.get(
    "/{workspace_id}/usage/model-calls",
    response_model = ModelUsageSummaryRead,
)
def get_model_call_usage_summary(
    workspace_id : int,
    db : Session = Depends(get_db),
    current_user : UserContext = Depends(
        require_roles(["admin", "developer", "viewer"])
    ),
)->dict:
    if workspace_id != current_user.workspace_id:
        raise HTTPException(status_code = 403, detail="workspace forbidden")
    
    service = ModelUsageService(db)
    return service.get_model_call_usage_summary(workspace_id = workspace_id)