from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class CreateShowCommand:
    title: str
    description: str | None = None
    duration_minutes: int
    age_rating: int
    poster_url: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PublishShowCommand:
    show_id: UUID
    