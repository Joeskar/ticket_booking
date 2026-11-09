from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class SeatState(StrEnum):
    FREE = "FREE"
    HELD = "HELD"  
    SOLD = "SOLD" 


class SeatRead(BaseModel):
    seat_id: UUID
    row_no: int
    seat_no: int
    seat_type: str
    state: SeatState
