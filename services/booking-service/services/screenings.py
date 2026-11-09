from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models import BookingStatus, Screening, ScreeningSeat
from repositories.processed_messages import ProcessedMessageRepository
from repositories.screenings import ScreeningRepository
from schemas.events import ScreeningPublished
from schemas.screenings import SeatRead, SeatState


async def apply_screening_published(session: AsyncSession, message_id: UUID, event: ScreeningPublished) -> bool:
    if not await ProcessedMessageRepository(session).try_mark(message_id, "ScreeningPublished"):
        return False

    screening = Screening(
        id=event.screening_id,
        show_id=event.show_id,
        hall_id=event.hall_id,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        price_amount=event.price_amount,
        price_currency=event.price_currency,
    )
    seats = [
        ScreeningSeat(
            screening_id=event.screening_id,
            seat_id=seat.seat_id,
            row_no=seat.row_no,
            seat_no=seat.seat_no,
            seat_type=seat.seat_type,
        )
        for seat in event.seats
    ]
    await ScreeningRepository(session).add(screening, seats)
    
    # отметка в processed_messages, screening и seats коммитятся атомарно, либо ничего из этого
    await session.commit()

    return True


_SEAT_STATE = {
    None: SeatState.FREE,
    BookingStatus.HELD: SeatState.HELD,
    BookingStatus.CONFIRMED: SeatState.SOLD,
}


async def list_seats(session: AsyncSession, screening_id: UUID) -> list[SeatRead]:
    screenings = ScreeningRepository(session)
    if await screenings.get(screening_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Screening not found")

    rows = await screenings.list_seats_with_booking_status(screening_id)
    return [
        SeatRead(
            seat_id=seat.seat_id,
            row_no=seat.row_no,
            seat_no=seat.seat_no,
            seat_type=seat.seat_type,
            state=_SEAT_STATE[status],
        )
        for seat, status in rows
    ]
