from fastapi_boot.core import Repository
from fastapi_boot.tortoise_utils import Select, Insert, Delete

from test_project.app1.src.modules.tortoise_utils.model import User, UserDTO, UserVO


# 函数装饰器
@Select('select * from {user}').fill(user=User.Meta.table)
async def get_all_user() -> list[UserVO]: ...

# 函数调用


async def get_user_by_name(name: str):
    return await Select('select * from {user} where name={name!r}').fill(user=User.Meta.table, name=name).execute(list[UserVO])


@Repository
class UserDao:

    # 方法装饰器
    @Insert("""
    insert into {table} (name,age) values({user.name!r}, {user.age})
    """).fill(table=User.Meta.table)
    async def create(self, user: UserDTO): ...

    async def delete_by_name(self, name: str):
        return await User.filter(name=name).delete()

    @Delete('delete from {table}').fill(table=User.Meta.table)
    async def clear(self): ...
