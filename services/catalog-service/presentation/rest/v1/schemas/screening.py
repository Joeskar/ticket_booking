from decimal import Decimal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field

from domain.value_objects import Currency


class ScreeningCreate(BaseModel):
    show_id: UUID
    hall_id: UUID
    starts_at: AwareDatetime
    price_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    price_currency: Currency
