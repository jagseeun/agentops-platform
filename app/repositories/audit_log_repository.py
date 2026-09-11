from typing import Any
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

class AuditLogRepository:
    def __init__(self, db:Session):
        self.db = db
    def create(
        self, *, workspace_id: int, actor_user_id : int, action: str, resource_type: str, resource_id: int, audit_metadata: dict[str, Any] | None = None,
    )->AuditLog:
        audit_log = AuditLog(
            workspace_id =workspace_id,
            actor_user_id = actor_user_id,
            action = action,
            resource_type = resource_type,
            resource_id = resource_id,
            audit_metadata = audit_metadata,
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log
    def list_by_workspace(self, *, workspace_id:int)->list[AuditLog]:
        return(
            self.db.query(AuditLog)
            .filter(AuditLog.workspace_id == workspace_id)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .all()
        )