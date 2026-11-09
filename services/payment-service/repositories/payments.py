from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models import Payment, PaymentAttempt


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def add(self, payment: Payment) -> None:
        self._session.add(payment)

    async def get_by_booking(self, booking_id: UUID) -> Payment | None:
        return await self._session.scalar(select(Payment).where(Payment.booking_id == booking_id))

    async def get_by_booking_for_update(self, booking_id: UUID) -> Payment | None:
        # тут используем select for update для блокировки 
        return await self._session.scalar(
            select(Payment).where(Payment.booking_id == booking_id).with_for_update()
        )

    async def get_attempt(self, payment_id: UUID, idempotency_key: str) -> PaymentAttempt | None:
        return await self._session.scalar(
            select(PaymentAttempt).where(
                PaymentAttempt.payment_id == payment_id,
                PaymentAttempt.idempotency_key == idempotency_key,
            )
        )

    async def list_attempts(self, payment_id: UUID) -> list[PaymentAttempt]:
        rows = await self._session.scalars(
            select(PaymentAttempt)
            .where(PaymentAttempt.payment_id == payment_id)
            .order_by(PaymentAttempt.created_at)
        )
        return list(rows)

    def add_attempt(self, attempt: PaymentAttempt) -> None:
        self._session.add(attempt)
