from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Workspace(Base):
    __tablename__="workspaces"

    id : Mapped[int] = mapped_column(primary_key=True, index=True)
    name : Mapped[str] = mapped_column(String(100), nullable=False)
    slug : Mapped[str] = mapped_column(String(80), unique = True, index=True, nullable=False)
    status : Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    