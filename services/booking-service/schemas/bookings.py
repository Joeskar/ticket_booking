from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from infrastructure.db.models import BookingStatus


class BookingCreate(BaseModel):
    screening_id: UUID
    seat_id: UUID


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    screening_id: UUID
    seat_id: UUID
    status: BookingStatus
    amount: Decimal
    currency: str
    expires_at: datetime
    created_at: datetime
