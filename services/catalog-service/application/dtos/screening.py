from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from domain.value_objects import Currency


@dataclass(frozen=True, kw_only=True)
class CreateScreeningCommand:
    hall_id: UUID
    show_id: UUID
    price_amount: Decimal
    price_currency: Currency
    starts_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class PublishScreeningCommand:
    screening_id: UUID
    