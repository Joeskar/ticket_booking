from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base
from infrastructure.db.mixins import TimeStampMixin


class Screening(Base, TimeStampMixin):
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )

    show_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )

    hall_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
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


class ScreeningSeat(Base):

    screening_id: Mapped[UUID] = mapped_column(
        ForeignKey("screenings.id"), primary_key=True
    )

    seat_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )

    row_no: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    seat_no: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    seat_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )
