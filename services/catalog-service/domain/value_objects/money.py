from typing import final
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from domain.value_objects.currency import Currency, CURRENCY_DECIMAL_PLACES
from domain.exceptions import CurrencyMismatchException, NegativeAmountException


@final
@dataclass(frozen=True, slots=True, kw_only=True, order=True)
class Money:
    value: Decimal
    currency: Currency
    
    def __post_init__(self):
        if self.value < 0:
            raise NegativeAmountException(f"Value must not be negative")
        
        decimal_places = CURRENCY_DECIMAL_PLACES[self.currency]
        quantum = Decimal(1).scaleb(-decimal_places)
        quantized_value = self.value.quantize(quantum, rounding=ROUND_HALF_UP)

        object.__setattr__(self, "value", quantized_value)
    
    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise CurrencyMismatchException(f"Cannot add {self.currency} and {other.currency}")
        
        return Money(value=self.value + other.value, currency=self.currency)
            
    def __str__(self) -> str:
        return f"{self.value} {self.currency}"
