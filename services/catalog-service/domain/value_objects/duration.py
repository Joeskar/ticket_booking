from typing import final
from dataclasses import dataclass

from domain.exceptions import NegativeNumberException


@final
@dataclass(frozen=True, slots=True, kw_only=True, order=True)
class Duration:
    value: int

    def __post_init__(self):
        if self.value < 0:
            raise NegativeNumberException(f"Value must not be negative")
