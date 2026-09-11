from typing import Literal
from pydantic import BaseModel, Field

UserRole = Literal["admin", "developer", "viewer"]

class UserContext(BaseModel):
    user_id : int = Field(ge=1)
    workspace_id : int = Field(ge=1)
    role: UserRole
    
    