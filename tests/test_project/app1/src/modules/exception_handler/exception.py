from typing import Annotated, Any
from annotated_doc import Doc
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_boot.core import ExceptionHandler


class NotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(404, 'Not Found')


@ExceptionHandler(NotFoundException)
def handler(request: Request, exp: NotFoundException):
    return JSONResponse(content={
        'code': exp.status_code,
        'msg': exp.detail,
    }, status_code=200)
