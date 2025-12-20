from typing import Annotated
from fastapi_boot.core import Bean, Inject
from test_project.src.modules.book.models import Book


@Bean('三国演义')
def fn1() -> Book:
    return Book(name='三国演义', author='罗贯中', price=100)


@Bean('水浒传')
def fn2() -> Book:
    return Book(name='水浒传', author='施耐庵', price=110)


@Bean('红楼梦')
def fn3() -> Book:
    return Book(name='红楼梦', author='曹雪芹', price=120)


@Bean('西游记')
def fn4() -> Book:
    return Book(name='西游记', author='吴承恩', price=130)


@Bean('四大名著')
def fn5(
    b1: Annotated[Book, '三国演义'],
    b2: Annotated[Book, '水浒传'],
) -> list[Book]:
    b3 = Inject(Book, '红楼梦')
    b4 = Inject.Qualifier('西游记')@Book
    return [b1, b2, b3, b4]


@Bean
def fn6(books: Annotated[list[Book], '四大名著']) -> tuple[Book, Book, Book, Book]:
    return (books[0], books[1], books[2], books[3])
