from decimal import Decimal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field


class SeatPayload(BaseModel):
    seat_id: UUID
    row_no: int
    seat_no: int
    seat_type: str


class ScreeningPublished(BaseModel):
    screening_id: UUID
    show_id: UUID
    hall_id: UUID
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    price_amount: Decimal
    price_currency: str = Field(min_length=3, max_length=3)
    seats: list[SeatPayload] = Field(min_length=1)


class BookingCreated(BaseModel):
    event_id: UUID
    occurred_at: AwareDatetime
    booking_id: UUID
    screening_id: UUID
    seat_id: UUID
    amount: Decimal
    currency: str
    expires_at: AwareDatetime


class BookingExpired(BaseModel):
    event_id: UUID
    occurred_at: AwareDatetime
    booking_id: UUID
    screening_id: UUID
    seat_id: UUID
    

class PaymentSucceeded(BaseModel):
    booking_id: UUID
    payment_id: UUID
    amount: Decimal
    currency: str