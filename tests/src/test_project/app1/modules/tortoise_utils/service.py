from dataclasses import dataclass
from fastapi_boot.core import Injectable
from .dao import (
    UserDao,
    get_all_user,
    get_user_by_name,
)
from .model import UserDTO


@Injectable
@dataclass
class UserService:
    user_dao: UserDao

    async def get_all(self):
        return await get_all_user()

    async def get_by_name(self, name: str):
        return await get_user_by_name(name)

    async def create(self, user: UserDTO):
        return await self.user_dao.create(user)

    async def delete_by_name(self, name: str):
        return await self.user_dao.delete_by_name(name)

    async def clear(self):
        return await self.user_dao.clear()
