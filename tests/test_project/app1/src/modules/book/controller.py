from dataclasses import dataclass
from fastapi_boot.core import Controller, Get, Prefix, Post, Delete, Put, use_dep
from test_project.app1.src.modules.book.service import BookService
from test_project.app1.src.modules.book.models import BookDTO
from test_project.app1.src.modules.book.hooks import use_path_book_name


@Controller('/book')
@dataclass
class BookController:
    book_service: BookService

    @Post()
    async def add_book(self, book: BookDTO):
        self.book_service.add_book(book)

    @Get('/cnt')
    async def get_book_cnt(self):
        return self.book_service.get_book_cnt()

    @Put()
    async def update_book(self, dto: BookDTO):
        return self.book_service.update_book(dto)

    @Prefix()
    @dataclass
    class NeedBookNamePathParamController:
        book_service: BookService
        book_name = use_dep(use_path_book_name)

        @Delete('/{name}')
        async def delete_book(self):
            return self.book_service.delete_book(self.book_name)

        @Get('/{name}')
        async def get_book(self):
            return self.book_service.get_book(self.book_name)
