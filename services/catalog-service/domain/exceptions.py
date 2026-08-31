# domain/exceptions.py
from typing import final


class DomainException(Exception):
    """Base domain exception"""


class DomainValidationException(DomainException):
    """Domain validation exceotion"""


class BusinessRuleViolationException(DomainException):
    """Business validation exception"""


#for VO objects
@final
class NegativeAmountException(DomainValidationException):
    """Raised when amount is negative"""


@final
class ScreeningInThePastException(DomainValidationException):
    """Raised when screening time is in the past"""


@final
class CurrencyMismatchException(BusinessRuleViolationException):
    """Raised when currencies don't match in an operation"""


#for entity objects
@final
class ScreeningAlreadyPublishedException(BusinessRuleViolationException):
    """Raised when trying to modify an already published screening"""
    