from sqlalchemy.orm import Session

from app.models.workflow import Workflow
from app.models.workflow_step import WorkflowStep
from app.schemas.workflow import WorkflowStepCreate
from app.models.agent import Agent
# create(self, *, workspace_id: int, name: str, steps: list[WorkflowStepCreate]) -> Workflow

#   안에서 해야 할 일:

#   1. Workflow 객체 만들기
#   2. db.add(workflow)
#   3. db.flush()
#   4. steps를 돌면서 WorkflowStep 객체 만들기
#   5. db.add(step)
#   6. db.commit()
#   7. db.refresh(workflow)
#   8. return workflow

#   여기서 새로 보는 건 flush()일 거야.

#   flush()는 commit 전인데, DB가 workflow.id를 먼저 만들어주게 하는 용도야.
#   왜 필요하냐면 step 만들 때 workflow_id=workflow.id가 필요하기 때문이야.

#   우선 직접 써보고 붙여줘. flush() 위치가 헷갈리면 그 부분만 물어봐.

class WorkflowRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, *, workspace_id: int, name: str, steps: list[WorkflowStepCreate],) -> Workflow:
        workflow=Workflow(
            workspace_id = workspace_id,
            name=name,
        )
        self.db.add(workflow)
        self.db.flush()
        
        for step in steps:
            workflow_step=WorkflowStep(
                workflow_id = workflow.id,
                agent_id=step.agent_id,
                step_order=step.step_order,
                input_mapping=step.input_mapping,
            )
            self.db.add(workflow_step)
            
        self.db.commit()
        self.db.refresh(workflow)
        return workflow
    
    
    def get_by_workspace_and_id(self, *, workspace_id:int, workflow_id:int,)->Workflow | None:
        return (
            self.db.query(Workflow)
            .filter(
                Workflow.workspace_id == workspace_id,
                Workflow.id==workflow_id,
            )
            .first()
        )
        
    def list_steps_with_agent(self, *, workflow_id:int,)->list[tuple[WorkflowStep, Agent]]:
        return(
            self.db.query(WorkflowStep, Agent)
            .join(Agent, WorkflowStep.agent_id == Agent.id)
            .filter(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.step_order)
            .all()
        )