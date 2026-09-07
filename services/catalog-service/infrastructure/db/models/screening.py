from datetime import datetime
from uuid import UUID

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base
from infrastructure.db.mixins import UuidMixin, TimeStampMixin


class Sreening(Base, UuidMixin, TimeStampMixin):
    status: Mapped[str] = mapped_column(
        String(32), nullable=False
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    
    show_id: Mapped[UUID] = mapped_column(
        ForeignKey("shows.id")
    )
    
    hall_id: Mapped[UUID] = mapped_column(
        ForeignKey("halls.id")
    )
    
    
