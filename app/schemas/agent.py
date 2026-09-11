from datetime import datetime

from pydantic import BaseModel, Field

class AgentCreate(BaseModel):
    workspace_id: int = Field(ge=1) #1 이상이어야함.
    name: str = Field(min_length=1, max_length=100)
    version: str=Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)
    
    
class AgentRead(BaseModel):
    id: int
    workspace_id: int
    name: str
    version: str
    description: str | None
    status: str
    created_at: datetime
    
    model_config = {"from_attributes" : True}