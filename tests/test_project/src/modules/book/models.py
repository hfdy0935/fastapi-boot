from pydantic import BaseModel, Field


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
