from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.session import async_session, get_session
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def get_uow() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(async_session)


UowDep = Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
