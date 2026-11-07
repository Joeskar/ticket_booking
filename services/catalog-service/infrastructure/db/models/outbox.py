from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from infrastructure.db.base import Base
from infrastructure.db.mixins import UuidMixin, TimeStampMixin


class OutBox(Base, UuidMixin, TimeStampMixin):
    __tablename__ = "outbox"
    
    message_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, nullable=False
    )
    
    aggregate_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    
    aggregate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    
    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )
    
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    __table_args__ = (
        Index("ix_outbox_unpublished", "created_at", postgresql_where=text("published_at IS NULL")),
    )
