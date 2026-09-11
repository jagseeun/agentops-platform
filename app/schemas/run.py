from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any

class RunCreate(BaseModel):
    input_payload: dict[str, Any] | None = None

class RunRead(BaseModel):
    id : int
    workflow_id : int
    workspace_id : int
    status: str
    input_payload: dict[str, Any] | None = None
    output_payload: dict[str, Any] | None = None
    error_message: str | None
    retry_count: int
    created_at: datetime
    started_at : datetime | None
    finished_at : datetime | None
    model_config = {"from_attributes": True}

class RunStatusUpdate(BaseModel):
    status : str = Field(min_length=1, max_length=20)