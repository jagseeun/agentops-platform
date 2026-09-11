from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, Integer,String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id : Mapped[int] = mapped_column(primary_key=True, index=True)
    
    workspace_id : Mapped[int] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable = False,
        index=True,
    )
    actor_user_id : Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    action : Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id : Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    audit_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True
    )
    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default=func.now(),
        nullable = False,
    )