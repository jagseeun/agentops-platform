from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Workflow(Base):
    __tablename__ = "workflows"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str]=mapped_column(String(20), default="draft", nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())