from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id : Mapped[int] = mapped_column(primary_key=True, index = True)
    data_source_id : Mapped[int] = mapped_column(
        ForeignKey("data_sources.id"),
        nullable=False,
        index = True,
    )
    workspace_id : Mapped[int] =mapped_column(
        ForeignKey("workspaces.id"),
        nullable = False,
        index = True
    )
    chunk_index : Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False)