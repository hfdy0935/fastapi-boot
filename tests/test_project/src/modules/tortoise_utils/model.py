from types import NoneType
from typing import Generic, TypeVar
from pydantic import BaseModel
from tortoise import Model
from tortoise import fields

T = TypeVar('T')


class BaseResp(BaseModel, Generic[T]):
    code: int = 200
    msg: str = ''
    data: T | NoneType = None


class User(Model):
    id = fields.IntField(primary_key=True, generated=True)
    name = fields.CharField(max_length=20)
    age = fields.IntField(ge=0)

    class Meta:
        table = 'user'


class UserVO(BaseModel):
    id: int
    name: str
    age: int


class UserDTO(UserVO):
    ...
