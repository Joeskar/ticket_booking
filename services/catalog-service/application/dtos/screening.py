from datetime import datetime
from dataclasses import dataclass
from uuid import UUID
from decimal import Decimal


@dataclass(frozen=True, kw_only=True)
class CreateScreeningCommand:
    hall_id: UUID
    show_id: UUID
    price_amount: Decimal
    price_currency: str
    starts_at: datetime
    user_id: int


@dataclass(frozen=True, slots=True, kw_only=True)
class PublishScreeningCommand:
    screening_id: UUID
    user_id: int
    