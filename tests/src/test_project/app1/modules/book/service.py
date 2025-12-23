from typing import Annotated
from fastapi_boot.core import Service, Inject, Autowired
from src.test_project.app1.modules.book.models import Book, BookDTO


@Service
class BookService:
    book4 = Autowired(Book, '西游记')

    def __init__(self, book1: Annotated[Book, '三国演义']) -> None:
        book2 = Inject(Book, '水浒传')
        book3 = Autowired(Book, '红楼梦')
        # 合集
        books1 = Inject(list[Book], '四大名著')
        books2 = Inject(tuple[Book, Book, Book, Book])
        assert books1[0] == books2[0] == book1
        assert books1[1] == books2[1] == book2
        assert books1[2] == books2[2] == book3
        assert books1[3] == books2[3] == self.book4
        self.book_store: dict[str, Book] = {book.name: book for book in books1}

    def exist_book(self, name: str):
        return name in self.book_store

    def add_book(self, dto: BookDTO):
        if self.exist_book(dto.name):
            return False
        self.book_store[dto.name] = Book.from_dto(dto)
        return True

    def delete_book(self, name: str):
        # if not self.exist_book(name):
        #     return False
        del self.book_store[name]
        return True

    def update_book(self, dto: BookDTO):
        if not self.exist_book(dto.name):
            return False
        self.book_store[dto.name].update(dto)
        return True

    def get_book(self, name: str):
        return self.book_store.get(name)

    def get_book_cnt(self):
        return len(self.book_store)
