from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.run_event_repository import RunEventRepository
from app.repositories.run_repository import RunRepository
from app.schemas.run_event import RunTimelineRead

class RunEventService:
    def __init__(self, db: Session):
        self.run_repository = RunRepository(db)
        self.run_event_repository = RunEventRepository(db)
        
    def get_timeline(self, *, workspace_id: int, run_id : int)-> RunTimelineRead:
        run=self.run_repository.get_by_workspace_and_id(
            workspace_id=workspace_id,
            run_id = run_id,
        )
        if not run:
            raise HTTPException(status_code=404, detail="run not found")
        events = self.run_event_repository.list_by_workspace_and_run(
            workspace_id=workspace_id,
            run_id=run_id,
        )
        return RunTimelineRead(
            run_id=run_id,
            events=[
                {
                    "event_type" : event.event_type,
                    "message" : event.message,
                    "event_metadata" : event.event_metadata,
                    "created_at" : event.created_at,
                }
                for event in events
            ],
        )
        