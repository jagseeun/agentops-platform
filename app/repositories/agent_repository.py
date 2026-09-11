from sqlalchemy.orm import Session
from app.models.agent import Agent

class AgentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_workspace_name_version(self, workspace_id : int, name : str, version : str)->Agent | None:
        return self.db.query(Agent).filter(Agent.workspace_id == workspace_id, Agent.name == name, Agent.version == version).first()
    
    def create(self, workspace_id : int, name : str, version : str, description : str | None) -> Agent:
        agent = Agent(workspace_id=workspace_id, name=name, version=version, description=description)
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent
    
    def list_by_workspace(
        self, 
        workspace_id: int,
        status: str | None = None,
    )-> list[Agent]:
        query = self.db.query(Agent).filter(Agent.workspace_id==workspace_id)
        
        if status is not None:
            query = query.filter(Agent.status == status)
        return query.all()
    
    def get_by_workspace_and_id(
        self,
        workspace_id: int,
        agent_id: int,
    )-> Agent | None :
        return(
            self.db.query(Agent)
            .filter(
                Agent.workspace_id==workspace_id,
                Agent.id==agent_id,
            )
            .first()
        )
    
    def deactivate(self, agent: Agent)->Agent:
        agent.status="inactive"
        self.db.commit()
        self.db.refresh(agent)
        return agent
    
        
        