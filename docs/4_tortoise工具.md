**封装了一些Tortoise操作数据库的装饰器**

:white_check_mark:**支持声明式、命令式**
:white_check_mark:**MyBatis？**
:white_check_mark:**Pydantic友好**


:hammer:`API`
- `Sql`
- `Select`
- `Update`
- `Insert`
- `Delete`

:bulb: `Sql`**是其他装饰器的基础装饰器**，其他装饰器是`Sql`装饰器的**语义化表达**，同时**返回值也做了处理**，和tortoise保持一致
:bulb: 支持**函数装饰器**、**方法装饰器**、**普通调用**三种方式

> `M`是`BaseModel`或`Model`

|  装饰器  |      返回值类型注解 / `execute`的参数      |                返回值                |
| :------: | :----------------------------------------: | :----------------------------------: |
|  `Sql`   |      `None` `tuple[int, list[dict]]`       |       `tuple[int, list[dict]]`       |
| `Select` | `M` `list[M]` `None or list or list[dict]` | `M or None`  `list[M]`  `list[dict]` |
| `Update` |              `None`     `int`              |                `int`                 |
| `Insert` |              `None`     `int`              |                `int`                 |
| `Delete` |              `None`     `int`              |                `int`                 |


:pushpin:关于返回值类型注解和`execute`的参数
```py
# 函数装饰器
@Select('select * from {user}').fill(user=User.Meta.table)
async def get_all_user() -> list[UserVO]: ... # list[UserVO]

# 函数调用
async def get_user_by_name(name: str):
    return await Select('select * from {user} where name={name}')\
        .fill(user=User.Meta.table, name=name)\
            .execute(list[UserVO]) # list[UserVO]

# 类实例的方法装饰器，这里的 sql 中可以获取到 self
@Delete('delete from {table}').fill(table=User.Meta.table)
    async def clear(self): ...
```