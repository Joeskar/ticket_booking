from uuid import UUID

from pydantic import BaseModel, Field


class HallCreate(BaseModel):
    venue_id: UUID
    name: str = Field(min_length=1, max_length=50)
    rows: int = Field(gt=0, le=100)
    seats_per_row: int = Field(gt=0, le=100)
