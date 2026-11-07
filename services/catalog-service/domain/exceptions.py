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
class NegativeNumberException(DomainValidationException):
    """Raised when number is negative"""
    

@final
class ScreeningInThePastException(DomainValidationException):
    """Raised when screening time is in the past"""
    

class InvalidAgeRatingException(DomainValidationException):
    ...
    
    
@final
class CurrencyMismatchException(BusinessRuleViolationException):
    """Raised when currencies don't match in an operation"""


#for entity objects
@final
class ScreeningAlreadyPublishedException(BusinessRuleViolationException):
    """Raised when trying to modify an already published screening"""


@final
class ScreeningAlreadyCancelledException(BusinessRuleViolationException):
    """Raised when trying to cancel an already cancelled screening"""

@final
class InvalidTimeRangeException(DomainValidationException):
    """Raised when start date later than end date"""


@final
class ShowNotPublishedException(BusinessRuleViolationException):
    """Raised when start date later than end date"""
    

class NotFoundException(DomainException):
    ...


@final
class ShowNotFoundException(NotFoundException):
    ...


@final
class ScreeningNotFoundException(NotFoundException):
    ...    
    

@final
class ShowAlreadyPublishedException(BusinessRuleViolationException):
    ...


@final
class HallHasNoSeatsException(BusinessRuleViolationException):
    ...
    