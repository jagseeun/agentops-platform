from datetime import datetime
from pydantic import BaseModel, Field

class DataSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    
class DataSourceRead(BaseModel):
    id : int
    workspace_id : int
    name: str
    status: str
    error_message: str | None
    created_at : datetime
    
    model_config = {"from_attributes" : True}