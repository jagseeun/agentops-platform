from sqlalchemy.orm import Session
from app.models.run import Run

class RunRepository:
    def __init__(self, db:Session):
        self.db = db
        
    def create(self, *, workflow_id:int, workspace_id:int, input_payload: dict|None)->Run:
        run=Run(
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            input_payload=input_payload,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
    
    def get_by_workspace_and_id(self, *, workspace_id: int, run_id : int)->Run | None:
        return (
            self.db.query(Run)
            .filter(
                Run.workspace_id==workspace_id,
                Run.id == run_id,
            )
            .first()
        )
    def update_status(self, *, run:Run, status: str)->Run:
        run.status = status
        self.db.commit()
        self.db.refresh(run)
        return run
    
    def save(self, run: Run) -> Run:
        self.db.commit()
        self.db.refresh(run)
        return run
    