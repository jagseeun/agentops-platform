from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.repositories.workspace_repository import WorkspaceRepository
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent import AgentCreate

class AgentService:
    def __init__(self, db: Session):
        self.workspace_repository = WorkspaceRepository(db)
        self.agent_repository = AgentRepository(db)
    
    def create_agent(self, payload: AgentCreate) -> Agent:
        existing = self.workspace_repository.get_by_id(payload.workspace_id)
        if not existing:
            raise HTTPException(status_code=404, detail="can't found workspace_id")
        #guard clause
        existing_agent = self.agent_repository.get_by_workspace_name_version(payload.workspace_id, payload.name, payload.version)
        if existing_agent:
            raise HTTPException(status_code=409, detail="already have same agent")
        return self.agent_repository.create(workspace_id=payload.workspace_id, name=payload.name, version=payload.version, description=payload.description)
    
    def list_agents(
        self,
        workspace_id: int,
        status: str | None = None,
    )->list[Agent]:
        existing = self.workspace_repository.get_by_id(workspace_id)
        
        if not existing:
            raise HTTPException(status_code=404, detail="workspace not found")
        
        return self.agent_repository.list_by_workspace(
            workspace_id=workspace_id,
            status=status
        )
    
    def deactivate_agent(
        self,
        workspace_id : int,
        agent_id : int,
    )->Agent:
        existing = self.workspace_repository.get_by_id(workspace_id)
        
        if not existing:
            raise HTTPException(status_code=404, detail="workspace not found")
        
        agent = self.agent_repository.get_by_workspace_and_id(
            workspace_id=workspace_id,
            agent_id=agent_id
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="agent not found")
        
        return self.agent_repository.deactivate(agent)
    
    