from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.workspace import Workspace
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate

class WorkspaceService:
    def __init__(self, db: Session):
        self.repository = WorkspaceRepository(db)
    
    def create_workspace(self, payload: WorkspaceCreate) -> Workspace:
        existing = self.repository.get_by_slug(payload.slug)

        if existing:
            raise HTTPException(status_code=409, detail="workspace slug already exists")
        
        return self.repository.create(name=payload.name, slug=payload.slug)