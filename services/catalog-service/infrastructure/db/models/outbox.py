from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from infrastructure.db.base import Base
from infrastructure.db.mixins import UuidMixin, TimeStampMixin


class OutBox(Base, UuidMixin, TimeStampMixin):
    message_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), default=uuid4, unique=True, nullable=False
    )
    
    aggregate_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    
    aggregate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, 
        unique=True, default=uuid4
    )
    
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    
    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )
    
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    