from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class RunEvent(Base):
    __tablename__ = "run_events"
    id : Mapped[int] = mapped_column(primary_key=True, index = True)
    workspace_id : Mapped[int] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable=False,
        index = True,
    )
    run_id : Mapped[int] = mapped_column(
        ForeignKey("runs.id"),
        nullable=False,
        index = True,
    )
    event_type : Mapped[str] = mapped_column(String(50), nullable=False, index = True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    event_metadata : Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )
    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default=func.now(),
        nullable=False,
    )
    