from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Run(Base):
    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"), nullable=False, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    status : Mapped[str] = mapped_column(String(20), default="queued", nullable=False)
    input_payload: Mapped[dict|None] = mapped_column(JSON, nullable=True)
    output_payload : Mapped[dict|None] = mapped_column(JSON, nullable=True)
    error_message : Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count : Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] =mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at : Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at : Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)