from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.model_call_repository import ModelCallRepository
from app.repositories.workspace_repository import WorkspaceRepository

class ModelUsageService:
    def __init__(self, db:Session):
        self.workspace_repository = WorkspaceRepository(db)
        self.model_call_repository = ModelCallRepository(db)
        
    def get_model_call_usage_summary(self, *, workspace_id : int) -> dict:
        workspace = self.workspace_repository.get_by_id(workspace_id)
        
        if not workspace:
            raise HTTPException(status_code=404, detail = "workspace not found")
        return self.model_call_repository.get_usage_summary_by_workspace(
            workspace_id = workspace_id
        )