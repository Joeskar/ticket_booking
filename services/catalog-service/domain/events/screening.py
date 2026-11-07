from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass

from domain.events.base import DomainEvent
from domain.shared.ids import ScreeningId, ShowId, HallId
from domain.value_objects import Currency, SeatInfo

@dataclass(frozen=True, kw_only=True)
class ScreeningPublished(DomainEvent):
    screening_id: ScreeningId
    show_id: ShowId
    hall_id: HallId
    starts_at: datetime
    ends_at: datetime
    price_amount: Decimal
    price_currency: Currency
    seats: tuple[SeatInfo, ...]

@dataclass(frozen=True, kw_only=True)
class ScreeningCancelled(DomainEvent):
    screening_id: ScreeningId