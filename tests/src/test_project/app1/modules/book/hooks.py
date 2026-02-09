from typing import Annotated
from fastapi import HTTPException, Path
from fastapi_boot.core import inject
from src.test_project.app1.modules.book.service import BookService


def use_path_book_name(name: Annotated[str, Path()]):
    """确保书名一定存在"""
    book_service = inject(BookService)
    if not book_service.exist_book(name):
        raise HTTPException(status_code=404, detail='Book Not Found')
    return name
