from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

class RunEventRead(BaseModel):
    event_type: str
    message: str
    metadata : dict[str, Any] | None = Field(default=None, alias = "event_metadata")
    created_at : datetime

class RunTimelineRead(BaseModel):
    run_id: int
    events: list[RunEventRead]