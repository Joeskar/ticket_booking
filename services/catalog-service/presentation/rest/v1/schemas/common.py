from uuid import UUID

from pydantic import BaseModel


class IdResponse(BaseModel):
    id: UUID
