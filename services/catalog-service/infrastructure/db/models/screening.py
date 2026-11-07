from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import String, DateTime, ForeignKey, Numeric, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base
from infrastructure.db.mixins import UuidMixin, TimeStampMixin
from domain.value_objects.statuses import ScreeningStatus


class Screening(Base, UuidMixin, TimeStampMixin):
    status: Mapped[ScreeningStatus] = mapped_column(
        SAEnum(ScreeningStatus, native_enum=False),
        nullable=False
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    
    price_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    
    price_currency: Mapped[str] = mapped_column(
        String(3), nullable=False
    )
    
    show_id: Mapped[UUID] = mapped_column(
        ForeignKey("shows.id")
    )
    
    hall_id: Mapped[UUID] = mapped_column(
        ForeignKey("halls.id")
    )
    
    
