from pydantic import BaseModel, Field


class VenueCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    city: str = Field(min_length=1, max_length=50)
    address: str = Field(min_length=1, max_length=100)
