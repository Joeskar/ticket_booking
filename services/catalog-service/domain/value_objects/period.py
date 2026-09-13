from typing import final
from datetime import datetime, timezone
from dataclasses import dataclass

from domain.exceptions import InvalidTimeRangeException

@final
@dataclass(frozen=True, kw_only=True, slots=True, order=True)
class Period:
    start: datetime
    end: datetime
    
    def __post_init__(self):
        # нормализация до часов, минут
        object.__setattr__(self, "start", self._normalize(self.start))
        object.__setattr__(self, "end", self._normalize(self.end))
        
        if self.end < self.start:
            raise InvalidTimeRangeException("End date must be later than start date")
        
    @staticmethod
    def _normalize(value: datetime) -> datetime:
        return value.astimezone(timezone.utc).replace(second=0, microsecond=0)
    
    def overlaps(self, other: "Period") -> bool:
        return self.start < other.end and other.start < self.end
    