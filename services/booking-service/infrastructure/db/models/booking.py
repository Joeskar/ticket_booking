from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, Numeric, String, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base
from infrastructure.db.mixins import TimeStampMixin, UuidMixin


class BookingStatus(StrEnum):
    HELD = "HELD"           
    CONFIRMED = "CONFIRMED" 
    EXPIRED = "EXPIRED"
    LATE_PAID = "LATE_PAID"


class Booking(Base, UuidMixin, TimeStampMixin):
    screening_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )

    seat_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )

    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, native_enum=False), nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3), nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["screening_id", "seat_id"],
            ["screening_seats.screening_id", "screening_seats.seat_id"],
        ),
        Index("ix_bookings_held_expires_at", "expires_at", postgresql_where=text("status = 'HELD'")),
        Index(
            "uq_bookings_active_seat",
            "screening_id",
            "seat_id",
            unique=True,
            postgresql_where=text("status NOT IN ('EXPIRED', 'LATE_PAID')"),
        ),
    )
