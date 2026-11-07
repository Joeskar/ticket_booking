from dataclasses import dataclass
from typing import final

from domain.shared.entity import AggregateRootEntity
from domain.shared.ids import ShowId
from domain.value_objects import Duration, AgeRating, ShowStatus
from domain.exceptions import ShowNotPublishedException, ShowAlreadyPublishedException


@dataclass(eq=False)
class ShowEntity(AggregateRootEntity):
    id: ShowId
    title: str
    duration: Duration
    age_rating: AgeRating
    status: ShowStatus = ShowStatus.DRAFT
    poster_url: str | None = None
    description: str | None = None
    
    @final
    def ensure_accepts_screenings(self) -> None:
        if self.status is not ShowStatus.PUBLISHED:
            raise ShowNotPublishedException(self.id)
        
    @final
    def publish(self) -> None:
        if self.status is not ShowStatus.DRAFT:
            raise ShowAlreadyPublishedException
        self.status = ShowStatus.PUBLISHED
        