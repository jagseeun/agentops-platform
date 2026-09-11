from sqlalchemy.orm import Session
from app.models.workspace import Workspace

class WorkspaceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_slug(self, slug: str)->Workspace | None:
        return self.db.query(Workspace).filter(Workspace.slug == slug).first()
    
    def get_by_id(self, workspace_id:int)->Workspace | None:
        return self.db.query(Workspace).filter(Workspace.id==workspace_id).first()
    
    def create(self, *, name:str, slug:str) -> Workspace:
        workspace = Workspace(name=name, slug=slug)
        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return workspace