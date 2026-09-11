from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.workflow import Workflow
from app.repositories.agent_repository import AgentRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workflow import WorkflowCreate, WorkflowDetailRead, WorkflowStepDetailRead

class WorkflowService:
    def __init__(self, db: Session):
        self.workspace_repository = WorkspaceRepository(db)
        self.agent_repository = AgentRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        
    def create_workflow(self, *, workspace_id:int, payload: WorkflowCreate)->Workflow:
        workspace= self.workspace_repository.get_by_id(workspace_id)
        
        if not workspace:
            raise HTTPException(status_code=404, detail="workspace not found")
        
        step_orders = [step.step_order for step in payload.steps]
        
        if step_orders[0] != 1:
            raise HTTPException(status_code=422, detail="step_order must start from 1")
        
        if len(step_orders) != len(set(step_orders)):
            raise HTTPException(status_code=422, detail="step_order duplicated")
        
        for step in payload.steps:
            agent = self.agent_repository.get_by_workspace_and_id(
                workspace_id = workspace_id,
                agent_id = step.agent_id,
            )
            if not agent:
                raise HTTPException(status_code=404, detail = "agent not found")
            
            if agent.status != "active":
                raise HTTPException(status_code=409, detail="inactive agent cannot be used")
            
        return self.workflow_repository.create(
            workspace_id = workspace_id,
            name = payload.name,
            steps=payload.steps,
        )
    
    def get_workflow(self, *, workspace_id: int, workflow_id: int,)->WorkflowDetailRead:
        workflow=self.workflow_repository.get_by_workspace_and_id(
            workspace_id = workspace_id,
            workflow_id = workflow_id,
        )
        if not workflow:
            raise HTTPException(status_code=404, detail="workflow not found")
        rows = self.workflow_repository.list_steps_with_agent(
            workflow_id = workflow_id,
        )
        
        steps = [
            WorkflowStepDetailRead(
                id = step.id,
                agent_id = agent.id,
                agent_name = agent.name,
                agent_version = agent.version,
                step_order=step.step_order
            )
            for step, agent in rows
        ]
        return WorkflowDetailRead(
            id = workflow.id,
            workspace_id = workflow.workspace_id,
            name = workflow.name,
            status = workflow.status,
            steps=steps
        )
