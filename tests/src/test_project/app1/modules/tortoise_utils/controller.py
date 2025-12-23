from dataclasses import dataclass
from typing import Annotated
from fastapi import Query
from fastapi_boot.core import Controller, Get, Post, Delete
from src.test_project.app1.modules.tortoise_utils.service import UserService
from src.test_project.app1.modules.tortoise_utils.model import BaseResp, UserDTO, UserVO
from src.test_project.app1.modules.tortoise_utils.expection import CreateUserFailException


@Controller('/user')
@dataclass
class UserController:
    user_service: UserService

    @Get('/all', response_model=BaseResp[list[UserVO]])
    async def get_all_user(self):
        users = await self.user_service.get_all()
        return BaseResp(data=users)

    @Get(response_model=BaseResp[list[UserVO]])
    async def get_user_by_name(self, name: Annotated[str, Query(description='用户名')]):
        users = await self.user_service.get_by_name(name)
        return BaseResp(data=users)

    @Post(response_model=BaseResp[int])
    async def create_user(self, dto: UserDTO):
        line_cnt = await self.user_service.create(dto)
        if line_cnt == 0:
            raise CreateUserFailException()
        return BaseResp(data=line_cnt)

    @Delete('/all', response_model=BaseResp[int])
    async def clear_users(self):
        cnt = await self.user_service.clear()
        return BaseResp(data=cnt)

    @Delete(response_model=BaseResp[int])
    async def delete_by_name(self, name: Annotated[str, Query(description='用户名')]):
        cnt = await self.user_service.delete_by_name(name)
        return BaseResp(data=cnt)
