from typing import final
from datetime import datetime
from dataclasses import dataclass

from domain.shared.entity import AggregateRootEntity
from domain.shared.ids import ScreeningId, HallId, ShowId
from domain.value_objects import Money, ScreeningStatus, Period
from domain.exceptions import ScreeningAlreadyPublishedException, ScreeningInThePastException, ScreeningAlreadyCancelledException
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
    def publish(self, now: datetime):
        if self.status != ScreeningStatus.DRAFT:
            raise ScreeningAlreadyPublishedException
        
        if self.period.start < now:
            raise ScreeningInThePastException
        
        self.status = ScreeningStatus.PUBLISHED
        self._add_event(ScreeningPublished(occurred_at=now, screening_id=self.id))
            
    @final
    def cancel(self, now: datetime):
        if self.status == ScreeningStatus.CANCELLED:
            raise ScreeningAlreadyCancelledException
        
        self.status = ScreeningStatus.CANCELLED
        self._add_event(ScreeningCancelled(occurred_at=now, screening_id=self.id))
    