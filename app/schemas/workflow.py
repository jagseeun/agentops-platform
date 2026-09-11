from datetime import datetime
from pydantic import BaseModel, Field

class WorkflowStepCreate(BaseModel):
    agent_id: int = Field(ge=1)
    step_order: int = Field(ge=1)
    input_mapping: str | None = None
    
class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    steps: list[WorkflowStepCreate] = Field(min_length=1)
    
class WorkflowStepRead(BaseModel):
    id:int
    workflow_id:int
    agent_id:int
    step_order: int
    input_mapping:str|None
    created_at: datetime
    
    model_config={"from_attributes":True}
    
class WorkflowRead(BaseModel):
    id: int
    workspace_id: int
    name: str
    status: str
    created_at: datetime
    steps: list[WorkflowStepRead] = []
    
    model_config = {"from_attributes" : True}


class WorkflowStepDetailRead(BaseModel):
    id: int
    agent_id: int
    agent_name: str
    agent_version: str
    step_order: int

class WorkflowDetailRead(BaseModel):
    id: int
    workspace_id: int
    name: str
    status: str
    steps: list[WorkflowStepDetailRead]