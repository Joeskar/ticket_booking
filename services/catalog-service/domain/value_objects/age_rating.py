from enum import IntEnum


class AgeRating(IntEnum):
    ZERO = 0
    SIX = 6
    TWELVE = 12
    SIXTEEN = 16
    EIGHTEEN = 18

    def __str__(self) -> str:
        return f"{self.value}+"
    