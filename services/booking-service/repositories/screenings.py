from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models import Booking, BookingStatus, Screening, ScreeningSeat
from repositories.bookings import IS_ACTIVE


class ScreeningRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, screening: Screening, seats: list[ScreeningSeat]) -> None:
        self._session.add(screening)
        await self._session.flush()
        self._session.add_all(seats)

    async def get(self, screening_id: UUID) -> Screening | None:
        return await self._session.get(Screening, screening_id)

    async def get_seat_for_update(self, screening_id: UUID, seat_id: UUID) -> ScreeningSeat | None:
        # тут использую select for update для блока место до конца транзакции
        return await self._session.get(ScreeningSeat, (screening_id, seat_id), with_for_update=True)

    async def list_seats_with_booking_status(
        self, screening_id: UUID
    ) -> list[tuple[ScreeningSeat, BookingStatus | None]]:
        rows = await self._session.execute(
            select(ScreeningSeat, Booking.status)
            .outerjoin(Booking, and_(
                Booking.screening_id == ScreeningSeat.screening_id,
                Booking.seat_id == ScreeningSeat.seat_id,
                IS_ACTIVE,
            ))
            .where(ScreeningSeat.screening_id == screening_id)
            .order_by(ScreeningSeat.row_no, ScreeningSeat.seat_no)
        )
        return [(seat, status) for seat, status in rows.tuples()]
