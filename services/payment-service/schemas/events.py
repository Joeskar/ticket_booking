from decimal import Decimal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel


class BookingCreated(BaseModel):
    booking_id: UUID
    amount: Decimal
    currency: str
    expires_at: AwareDatetime


class BookingExpired(BaseModel):
    booking_id: UUID


class PaymentSucceeded(BaseModel):
    event_id: UUID
    occurred_at: AwareDatetime
    payment_id: UUID
    booking_id: UUID
    attempt_id: UUID
    amount: Decimal
    currency: str
