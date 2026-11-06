from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class CreateShowCommand:
    title: str
    descrtiption: str | None = None
    duration: int
    age_rating: str
    poster_url: str
    user_id: int
