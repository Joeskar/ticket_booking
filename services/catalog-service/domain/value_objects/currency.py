from enum import StrEnum


class Currency(StrEnum):
    KZT = "KZT"
    USD = "USD"


CURRENCY_DECIMAL_PLACES: dict[Currency, int] = {
    Currency.KZT: 2,
    Currency.USD: 2,
}
