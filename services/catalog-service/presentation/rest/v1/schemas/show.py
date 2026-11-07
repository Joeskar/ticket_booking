from pydantic import BaseModel, Field

from domain.value_objects import AgeRating


class ShowCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    duration_minutes: int = Field(gt=0)
    age_rating: AgeRating
    poster_url: str | None = Field(default=None, max_length=500)
