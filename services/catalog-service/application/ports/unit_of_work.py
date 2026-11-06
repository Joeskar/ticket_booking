from typing import Protocol

from application.ports.outbox import OutBox
from domain.repositories.show import ShowRepository
from domain.repositories.screening import ScreeningRepository


class UnitOfWork(Protocol):
    screenings_repo: ScreeningRepository
    shows_repo: ShowRepository
    outbox: OutBox
    
    async def __aenter__(self):
        ...
        
    async def __aexit__(self, exc_type, exc, tb):
        ...
        
    async def commit(self):
        ...
        
    async def rollback(self):
        ...
        