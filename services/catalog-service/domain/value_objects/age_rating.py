from typing import final
from dataclasses import dataclass

from exceptions import InvalidAgeRatingException


ALLOWED_MIN_AGES: frozenset[int] = frozenset({0, 6, 12, 16, 18})


@final
@dataclass(frozen=True, kw_only=True)
class AgeRating:
    value: int
    
    def __post_init__(self):
        if self.value not in ALLOWED_MIN_AGES:
            raise InvalidAgeRatingException("Unsuporrted age rating")
        