from uuid import UUID

from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base
from infrastructure.db.mixins import UuidMixin


class Hall(Base, UuidMixin):
    name: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    
    venue_id: Mapped[UUID] = mapped_column(
        ForeignKey("venues.id")
    )
    

class HallSeat(Base, UuidMixin):
    hall_id: Mapped[UUID] = mapped_column(
        ForeignKey("halls.id")
    )
    
    name: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    
    name: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    
    row_no: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    
    seat_no: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    
    seat_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )
    
    