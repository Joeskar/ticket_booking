from dataclasses import dataclass
from typing import final

from domain.shared.entity import AggregateRootEntity
from domain.shared.ids import ShowId
from domain.value_objects import Duration, AgeRating, ShowStatus
from domain.exceptions import ShowNotPublishedException


@dataclass(eq=False)
class ShowEntity(AggregateRootEntity):
    id: ShowId
    title: str
    duration: Duration
    age_rating: AgeRating
    poster_url: str
    status: ShowStatus = ShowStatus.DRAFT
    description: str | None = None
    
    def __post_init__(self):
        ...
    
    @final
    def ensure_accepts_screenings(self) -> None:
        if self.status is not ShowStatus.PUBLISHED:
            raise ShowNotPublishedException(self.id)
        