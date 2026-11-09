from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure import payment_service
from infrastructure.db.models import AttemptStatus, Payment, PaymentAttempt, PaymentStatus
from repositories.outbox import OutboxRepository
from repositories.payments import PaymentRepository
from repositories.processed_messages import ProcessedMessageRepository
from schemas.events import BookingCreated, BookingExpired, PaymentSucceeded
from schemas.payments import AttemptRead, PaymentRead, PayRequest

ATTEMPT_CONSTRAINTS = {"uq_payment_attempts_key", "uq_payment_attempts_one_success"}


class PaymentNotRegisteredYet(Exception):
    ...


async def register_booking(session: AsyncSession, message_id: UUID, event: BookingCreated) -> bool:
    if not await ProcessedMessageRepository(session).try_mark(message_id, "BookingCreated"):
        return False

    PaymentRepository(session).add(Payment(
        id=uuid4(),
        booking_id=event.booking_id,
        amount=event.amount,
        currency=event.currency,
        status=PaymentStatus.PENDING,
        expires_at=event.expires_at,
    ))
    await session.commit()
    return True


async def close_expired_booking(session: AsyncSession, message_id: UUID, event: BookingExpired) -> PaymentStatus | None:
    if not await ProcessedMessageRepository(session).try_mark(message_id, "BookingExpired"):
        return None

    payment = await PaymentRepository(session).get_by_booking_for_update(event.booking_id)
    if payment is None:
        # откатится вместе с отметкой в processed_messages, сообщение придёт снова
        raise PaymentNotRegisteredYet(event.booking_id)

    if payment.status == PaymentStatus.PENDING:
        payment.status = PaymentStatus.EXPIRED
        
    result = payment.status
    await session.commit()
    return result



async def pay(session: AsyncSession, booking_id: UUID, idempotency_key: str, request: PayRequest) -> PaymentAttempt:
    """попытка оплаты, используем idempotency_key, если приходит тот же idempotency_key, то возвращаем ту же попытку"""
    payments = PaymentRepository(session)

    payment = await payments.get_by_booking_for_update(booking_id)
    if payment is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Payment is not available yet, retry later")

    # тут идет повтор, если с таким ключем уже был запрос, то возвращаем его
    existing = await payments.get_attempt(payment.id, idempotency_key)
    if existing is not None:
        return existing

    if payment.status == PaymentStatus.SUCCEEDED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Booking is already paid")
    now = datetime.now(timezone.utc)
    if payment.status == PaymentStatus.EXPIRED or now >= payment.expires_at:
        raise HTTPException(status.HTTP_409_CONFLICT, "Booking has expired")

    result = await payment_service.charge(
        amount=payment.amount,
        currency=payment.currency,
        card_number=request.card_number,
        delay_seconds=request.delay_seconds,
    )

    attempt = PaymentAttempt(
        id=uuid4(),
        payment_id=payment.id,
        idempotency_key=idempotency_key,
        status=AttemptStatus.SUCCEEDED if result.approved else AttemptStatus.FAILED,
        card_last4=request.card_number[-4:],
        failure_reason=result.failure_reason,
        provider_ref=result.provider_ref,
        created_at=now,
    )
    payments.add_attempt(attempt)

    if result.approved:
        payment.status = PaymentStatus.SUCCEEDED
        event = PaymentSucceeded(
            event_id=uuid4(),
            occurred_at=now,
            payment_id=payment.id,
            booking_id=booking_id,
            attempt_id=attempt.id,
            amount=payment.amount,
            currency=payment.currency,
        )
        OutboxRepository(session).put(
            message_id=event.event_id,
            event_type="PaymentSucceeded",
            aggregate_type="payment",
            aggregate_id=payment.id,
            payload=event.model_dump(mode="json"),
        )

    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        # # страховка, если блокировку обошли, индексы в БД не дадут записать вторую попытку с тем же ключом
        if _violated_constraint(error) in ATTEMPT_CONSTRAINTS:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Concurrent payment for this booking, retry with the same key"
            ) from error
        raise
    return attempt


async def get_payment(session: AsyncSession, booking_id: UUID) -> PaymentRead:
    payments = PaymentRepository(session)
    payment = await payments.get_by_booking(booking_id)
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")

    attempts = await payments.list_attempts(payment.id)
    return PaymentRead(
        id=payment.id,
        booking_id=payment.booking_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        expires_at=payment.expires_at,
        attempts=[AttemptRead.model_validate(a) for a in attempts],
    )


def _violated_constraint(error: IntegrityError) -> str | None:
    driver_error = getattr(error.orig, "__cause__", None)
    return getattr(driver_error, "constraint_name", None)
