from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models import Booking, BookingStatus

# активный, если статус не expired и late_paid
IS_ACTIVE = Booking.status.not_in([BookingStatus.EXPIRED, BookingStatus.LATE_PAID])


class BookingRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, booking_id: UUID) -> Booking | None:
        return await self._session.get(Booking, booking_id)
    
    async def get_for_update(self, booking_id: UUID) -> Booking | None:
        return await self._session.get(Booking, booking_id, with_for_update=True)

    async def has_active(self, screening_id: UUID, seat_id: UUID) -> bool:
        found = await self._session.scalar(
            select(Booking.id)
            .where(Booking.screening_id == screening_id, Booking.seat_id == seat_id, IS_ACTIVE)
            .limit(1)
        )
        return found is not None
    
    async def list_due_for_update(self, now: datetime, limit: int) -> list[Booking]:
        rows = await self._session.scalars(
            select(Booking)
            .where(Booking.status == BookingStatus.HELD, Booking.expires_at <= now)
            .order_by(Booking.expires_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(rows)

    def add(self, booking: Booking) -> None:
        self._session.add(booking)
