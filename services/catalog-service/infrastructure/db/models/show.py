from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base
from infrastructure.db.mixins import UuidMixin


class Show(Base, UuidMixin):
    title: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    
    description: Mapped[str] = mapped_column(
        String(150), nullable=True
    )
    
    duration_min: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    
    age_rating: Mapped[str] = mapped_column(
        String(15), nullable=False
    )
    
    poster_url: Mapped[str] = mapped_column(
        String(100), nullable=True
    )
    
    