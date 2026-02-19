from typing import Annotated

from pydantic import BaseModel, Field
from fastapi_boot.core import Bean

globalId = 0


def get_id():
    global globalId
    globalId += 1
    return globalId


class BookDTO(BaseModel):
    name: str = Field(max_length=10)
    author: str
    price: int | float = Field(gt=0)


class Book(BookDTO):
    id: int = Field(default_factory=get_id)

    def update(self, dto: BookDTO):
        self.name = self.name if dto.name is None else dto.name
        self.author = self.author if dto.author is None else dto.author
        self.price = self.price if dto.price is None else dto.price
        return self

    @classmethod
    def from_dto(cls, dto: BookDTO):
        return cls(**dto.model_dump())


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
    book1: Annotated[Book, '三国演义'],
    book2: Annotated[Book, '水浒传'],
    book3: Annotated[Book, '红楼梦'],
    book4: Annotated[Book, '西游记'],
) -> list[Book]:
    return [book1, book2, book3, book4]
