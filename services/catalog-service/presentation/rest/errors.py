from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from domain.exceptions import (
    BusinessRuleViolationException,
    DomainValidationException,
    NotFoundException,
)


def _domain_handler(status_code: int):
    async def handle(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"code": type(exc).__name__})
    return handle


async def _integrity_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=409, content={"code": "IntegrityError"})


def install_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundException, _domain_handler(404))
    app.add_exception_handler(BusinessRuleViolationException, _domain_handler(409))
    app.add_exception_handler(DomainValidationException, _domain_handler(422))
    app.add_exception_handler(IntegrityError, _integrity_handler)
