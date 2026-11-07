from sqlalchemy import String, Integer, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base
from infrastructure.db.mixins import UuidMixin
from domain.value_objects.statuses import ShowStatus



class Show(Base, UuidMixin):
    title: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    
    duration_min: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    
    status: Mapped[ShowStatus] = mapped_column(
        SAEnum(ShowStatus, native_enum=False),
        nullable=False
    )
    
    age_rating: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    
    poster_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    
    