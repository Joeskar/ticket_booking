import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from infrastructure.db.models import Booking, BookingStatus
from repositories.bookings import BookingRepository
from repositories.outbox import OutboxRepository
from repositories.processed_messages import ProcessedMessageRepository
from repositories.screenings import ScreeningRepository
from schemas.events import BookingCreated, BookingExpired, PaymentSucceeded

log = logging.getLogger("booking.service")

# создания букинга
async def create_booking(session: AsyncSession, screening_id: UUID, seat_id: UUID) -> Booking:
    screenings = ScreeningRepository(session)
    bookings = BookingRepository(session)

    screening = await screenings.get(screening_id)
    if screening is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Screening not found")

    now = datetime.now(timezone.utc)
    if screening.starts_at <= now:
        raise HTTPException(status.HTTP_409_CONFLICT, "Screening has already started")

    # параллельная бронь этого же места ждёт здесь, пока мы не сделаем commit или rollback
    seat = await screenings.get_seat_for_update(screening_id, seat_id)
    if seat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Seat not found")

    # проверка идёт уже под блокировкой, видим бронь, которую закоммитил тот, кого мы ждали
    if await bookings.has_active(screening_id, seat_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Seat is already booked")

    booking = Booking(
        id=uuid4(),
        screening_id=screening_id,
        seat_id=seat_id,
        status=BookingStatus.HELD,
        amount=screening.price_amount,
        currency=screening.price_currency,
        expires_at=now + timedelta(seconds=settings.booking.hold_ttl_seconds),
        created_at=now,
    )
    bookings.add(booking)

    event = BookingCreated(
        event_id=uuid4(),
        occurred_at=now,
        booking_id=booking.id,
        screening_id=screening_id,
        seat_id=seat_id,
        amount=booking.amount,
        currency=booking.currency,
        expires_at=booking.expires_at,
    )
    OutboxRepository(session).put(
        message_id=event.event_id,
        event_type="BookingCreated",
        aggregate_type="booking",
        aggregate_id=booking.id,
        payload=event.model_dump(mode="json"),
    )

    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        # страховка на случай, если блокировку обошли, то у нас есть индекс на уровне БД, который не даст создать вторую активную бронь на место, если там статус не EXPIRED или LATE_PAID 
        if _violated_constraint(error) == "uq_bookings_active_seat":
            raise HTTPException(status.HTTP_409_CONFLICT, "Seat is already booked") from error
        raise
    return booking


async def get_booking(session: AsyncSession, booking_id: UUID) -> Booking:
    booking = await BookingRepository(session).get(booking_id)
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    return booking


def _violated_constraint(error: IntegrityError) -> str | None:
    driver_error = getattr(error.orig, "__cause__", None)
    return getattr(driver_error, "constraint_name", None)


# оплата прошла
async def apply_payment_succeeded(session: AsyncSession, message_id: UUID, event: PaymentSucceeded) -> BookingStatus | None:
    if not await ProcessedMessageRepository(session).try_mark(message_id, "PaymentSucceeded"):
        return None

    bookings = BookingRepository(session)
    # та же строка, что берёт таймер, оплата и истечение одной брони идут по очереди
    booking = await bookings.get_for_update(event.booking_id)
    if booking is None:
        raise ValueError(f"booking {event.booking_id} not found")

    if booking.status == BookingStatus.HELD:
        booking.status = BookingStatus.CONFIRMED
    elif booking.status == BookingStatus.EXPIRED:
        # оплата пришла после истечения, если место еще свободно, то подтверждаем, если нет, то возврат денег
        await ScreeningRepository(session).get_seat_for_update(booking.screening_id, booking.seat_id)
        if await bookings.has_active(booking.screening_id, booking.seat_id):
            booking.status = BookingStatus.LATE_PAID
            log.warning("booking %s paid after expiry, seat is taken: refund payment %s", booking.id, event.payment_id)
        else:
            booking.status = BookingStatus.CONFIRMED

    result = booking.status
    await session.commit()
    return result


# срок брони прошел
async def expire_due_holds(session: AsyncSession, limit: int) -> int:
    """тут мы атомарно делаем update статуса записи на expired и создаем сущность outbox, а потом через relay отправляются событие BookingExpired"""
    now = datetime.now(timezone.utc)
    due = await BookingRepository(session).list_due_for_update(now, limit)

    outbox = OutboxRepository(session)
    for booking in due:
        booking.status = BookingStatus.EXPIRED
        event = BookingExpired(
            event_id=uuid4(),
            occurred_at=now,
            booking_id=booking.id,
            screening_id=booking.screening_id,
            seat_id=booking.seat_id,
        )
        outbox.put(
            message_id=event.event_id,
            event_type="BookingExpired",
            aggregate_type="booking",
            aggregate_id=booking.id,
            payload=event.model_dump(mode="json"),
        )

    await session.commit()
    return len(due)

