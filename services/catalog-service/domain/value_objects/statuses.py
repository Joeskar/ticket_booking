from enum import StrEnum


class ScreeningStatus(StrEnum):
    DRAFT = "DFAFT"
    PUBLISHED = "PUBLISHED"
    CANCELLED = "CANCELLED"


class ShowStatus(StrEnum):
    DRAFT = "DFAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    