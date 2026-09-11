from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.repositories.audit_log_repository import AuditLogRepository

from app.db.session import get_db
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentRead
from app.services.agent_service import AgentService
from app.api.deps import require_roles
from app.core.security import UserContext
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
def current_agent(payload: AgentCreate, db: Session=Depends(get_db), current_user:UserContext=Depends(require_roles(["admin"])))-> Agent:
    if payload.workspace_id != current_user.workspace_id:
        raise HTTPException(
            status_code = 403,
            detail="workspace forbidden"
        )
    service = AgentService(db)
    agent = service.create_agent(payload)
    
    AuditLogRepository(db).create(
        workspace_id = agent.workspace_id,
        actor_user_id=current_user.user_id,
        action = "create_agent",
        resource_type="Agent",
        resource_id=agent.id,
        audit_metadata={
            "name": agent.name,
            "version" : agent.version,
        },
    )
    return agent
