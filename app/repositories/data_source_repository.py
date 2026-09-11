from sqlalchemy.orm import Session
from app.models.data_source import DataSource

class DataSourceRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def create(
        self, *, workspace_id: int, name: str, status: str = "completed",
    )->DataSource:
        data_source = DataSource(
            workspace_id = workspace_id,
            name = name,
            status = status
        )
        self.db.add(data_source)
        self.db.commit()
        self.db.refresh(data_source)
        
        return data_source