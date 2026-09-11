from datetime import datetime

from pydantic import BaseModel, Field

class WorkspaceCreate(BaseModel):
    name : str = Field(min_length=1, max_length=100)
    slug : str = Field(min_length=2, max_length=80)

class WorkspaceRead(BaseModel):
    id: int
    name: str
    slug: str
    status : str
    created_at : datetime

    model_config = {"from_attributes" : True}