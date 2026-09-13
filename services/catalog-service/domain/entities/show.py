from dataclasses import dataclass

from domain.shared.entity import AggregateRootEntity
from domain.value_objects import Duration, AgeRating, ShowStatus


@dataclass
class ShowEntity(AggregateRootEntity):
    title: str
    duration: Duration
    age_rating: AgeRating
    poster_url: str
    status: ShowStatus = ShowStatus.DRAFT
    description: str | None = None
    
    def __post_init__(self):
        ...
        