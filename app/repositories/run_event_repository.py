from typing import Any
from sqlalchemy.orm import Session
from app.models.run_event import RunEvent

class RunEventRepository:
    def __init__(self, db:Session):
        self.db = db
    def create(
        self, *, workspace_id : int, run_id : int, event_type: str, message: str, event_metadata: dict[str, Any]| None = None,
    )->RunEvent:
        event = RunEvent(
            workspace_id=workspace_id,
            run_id = run_id,
            event_type = event_type,
            message=message,
            event_metadata = event_metadata
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event
    def list_by_workspace_and_run(
        self, *,  workspace_id: int, run_id: int,
    )->list[RunEvent]:
        return (
            self.db.query(RunEvent)
            .filter(
                RunEvent.workspace_id == workspace_id,
                RunEvent.run_id == run_id,
            )
            .order_by(RunEvent.created_at.asc(), RunEvent.id.asc())
            .all()
        )