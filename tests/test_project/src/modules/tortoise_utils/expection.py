from typing import Any, Dict
from fastapi import HTTPException, Request
from fastapi_boot.core import ExceptionHandler

from test_project.src.modules.tortoise_utils.model import BaseResp


class CreateUserFailException(HTTPException):
    def __init__(self, status_code: int = 500, detail: Any = None, headers: Dict[str, str] | None = None) -> None:
        super().__init__(status_code, detail, headers)


@ExceptionHandler(CreateUserFailException)
def handle_create_user_failed(request: Request, exp: CreateUserFailException):
    return BaseResp(code=500, msg='创建失败')
