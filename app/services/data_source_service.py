from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.repositories.data_source_repository import DataSourceRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.data_source import DataSourceCreate

class DataSourceService:
    def __init__(self, db: Session):
        self.data_source_repository = DataSourceRepository(db)
        self.workspace_repository = WorkspaceRepository(db)
        
    def create_data_source(
        self,
        *,
        workspace_id : int,
        payload: DataSourceCreate,
    )->DataSource:
        workspace = self.workspace_repository.get_by_id(workspace_id)
            
        if not workspace:
            raise HTTPException(status_code=404, detail="workspace not found")
            
        return self.data_source_repository.create(
            workspace_id = workspace_id,
            name = payload.name,
            status = "completed",
        )