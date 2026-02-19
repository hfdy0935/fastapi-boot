from typing import Annotated

from fastapi_boot.core import Injectable
from src.test_project.app1.modules.book.models import Book, BookDTO


@Injectable
class BookService:

    def __init__(self, books: Annotated[list[Book], '四大名著']) -> None:
        self.books = {book.name: book for book in books}

    def exist_book(self, name: str):
        return name in self.books

    def add_book(self, dto: BookDTO):
        if self.exist_book(dto.name):
            return False
        self.books[dto.name] = Book.from_dto(dto)
        return True

    def delete_book(self, name: str):
        # if not self.exist_book(name):
        #     return False
        del self.books[name]
        return True

    def update_book(self, dto: BookDTO):
        if not self.exist_book(dto.name):
            return False
        self.books[dto.name].update(dto)
        return True

    def get_book(self, name: str):
        return self.books.get(name)

    def get_book_cnt(self):
        return len(self.books)
