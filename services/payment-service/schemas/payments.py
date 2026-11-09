from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from infrastructure.db.models import AttemptStatus, PaymentStatus


class PayRequest(BaseModel):
    card_number: str = Field(pattern=r"^\d{12,19}$", examples=["4242424242424242", "4000000000000002"])
    delay_seconds: float = Field(0, ge=0, le=30, description="Имитация медленного провайдера")


class AttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payment_id: UUID
    idempotency_key: str
    status: AttemptStatus
    card_last4: str
    failure_reason: str | None
    created_at: datetime


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    expires_at: datetime
    attempts: list[AttemptRead]
