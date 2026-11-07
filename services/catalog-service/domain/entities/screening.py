from collections.abc import Sequence
from typing import final
from datetime import datetime
from dataclasses import dataclass

from domain.shared.entity import AggregateRootEntity
from domain.shared.ids import ScreeningId, HallId, ShowId
from domain.value_objects import Money, ScreeningStatus, Period, SeatInfo
from domain.exceptions import ScreeningAlreadyPublishedException, ScreeningInThePastException, ScreeningAlreadyCancelledException, HallHasNoSeatsException
from domain.events.screening import ScreeningPublished, ScreeningCancelled


@dataclass(eq=False)
class ScreeningEntity(AggregateRootEntity):
    id: ScreeningId
    hall_id: HallId
    show_id: ShowId
    money: Money
    period: Period
    status: ScreeningStatus = ScreeningStatus.DRAFT
    
    @final
    def publish(self, now: datetime, seats: Sequence[SeatInfo]):
        if self.status != ScreeningStatus.DRAFT:
            raise ScreeningAlreadyPublishedException
        
        if self.period.start < now:
            raise ScreeningInThePastException

        if not seats:
            raise HallHasNoSeatsException
        
        self.status = ScreeningStatus.PUBLISHED
        self._add_event(ScreeningPublished(
            occurred_at=now,
            aggregate_id=self.id,
            aggregate_type="screening",
            screening_id=self.id,
            show_id=self.show_id,
            hall_id=self.hall_id,
            starts_at=self.period.start,
            ends_at=self.period.end,
            price_amount=self.money.value,
            price_currency=self.money.currency,
            seats=tuple(seats),
        ))
            
    @final
    def cancel(self, now: datetime):
        if self.status == ScreeningStatus.CANCELLED:
            raise ScreeningAlreadyCancelledException
        
        self.status = ScreeningStatus.CANCELLED
        self._add_event(ScreeningCancelled(
            occurred_at=now,
            screening_id=self.id,
            aggregate_id=self.id,
            aggregate_type="screening"
        ))
    