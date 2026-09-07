from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base
from infrastructure.db.mixins import UuidMixin, TimeStampMixin


class Venue(Base, UuidMixin, TimeStampMixin):
    name: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    
    city: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    
    address: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    