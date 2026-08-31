from typing import NewType
from uuid import UUID


VenueId = NewType("VenueId", UUID)
HallId = NewType("HallId", UUID)
ScreeningId = NewType("ScreeningId", UUID)
ShowId = NewType("ShowId", UUID)
