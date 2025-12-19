from collections.abc import Callable, Coroutine, Mapping, Sequence
from functools import wraps
from inspect import signature
import inspect
import json
import re
from typing import Any, ParamSpec, TypeVar, cast, get_args, get_origin, overload
from warnings import warn
from pydantic import BaseModel
from tortoise import Model, Tortoise
from tortoise.backends.sqlite.client import SqliteClient


def get_func_params_dict(func: Callable, *args, **kwds):
    """get params of func when calling

    Args:
        func (Callable)

    Returns:
        _type_: dict
    """
    res = {}
    for i, (k, v) in enumerate(signature(func).parameters.items()):
        if v.default != inspect._empty:
            res.update({k: v.default})
        elif len(args) > i:
            res.update({k: args[i]})
        else:
            res.update({k: kwds.get(k)})
    return res


def get_is_sqlite(connection_name: str):
    conn = Tortoise.get_connection(connection_name)
    return conn.__class__ == SqliteClient


def parse_item(v):
    """parse an item"""
    if isinstance(v, str):
        try:
            t1 = json.loads(v)
            if isinstance(t1, dict):
                return parse_execute_res(t1)
            elif isinstance(t1, list):
                return [parse_item(i) for i in t1]
            else:
                return v
        except:
            return v
    else:
        return v


def parse_execute_res(target: dict):
    """parse JSONField"""
    return {k: parse_item(v) for k, v in target.items()}


PM = TypeVar('PM', bound=BaseModel)
TM = TypeVar('TM', bound=Model)
P = ParamSpec('P')


class Sql:
    """execute raw sql, always return (effect rows nums, result list[dict])
    - 被装饰的函数/方法有个参数：fill_with_repr，表示是否保留字符串的引号，防止字符串参数按照整数查询(如'1')或报错('a')，默认True
    >>> Params
        sql: 原始sql语句，用{变量名}占位，可以在.fill(xxx=xxx)、.fill_map(dict)和被装饰的函数中传参填充，传表名的话建议在前二者中传
        connection_name: Tortoise.get_connection(connection_name)的参数, default 'default'

    >>> Example
    ```python
    @Sql('select * from user where id={id}')
    async def get_user_by_id(id: str) -> tuple[int, list[dict[str, Any]]]:...

    class Bar:
        @Sql('select * from user where id={dto.id} and name={dto.name}')
        async def get_user(self, dto: UserDTO):...


    # the result will be like (1, {'id': 0, 'name': 'foo', 'age': 20})
    ```
    """

    def __init__(self, sql: str, connection_name: str = 'default'):
        self.sql = sql
        self.connection_name = connection_name
        self.pattern = re.compile(r'\{\s*(.*?)\s*\}')

    @property
    def is_sqlite(self):
        return get_is_sqlite(self.connection_name)

    @property
    def placeholder(self):
        return '?' if self.is_sqlite else '%s'

    def fill(self, fill_with_repr: bool = True, **kwds):
        """向sql语句中填充变量
        - `fill_with_repr`，表示是否保留字符串的引号，防止字符串参数按照整数查询(如'1')或报错('a')，默认True
        >>> Example

        ```python
        @Repository
        class _:
            NORMAL = 1
            FORBID = 0

            @Sql('
                select * from {user_table} where status={self.NORMAL}
            ').fill(user_table=UserDO.Meta.table)
            async def get_normal_users(self):
        ```

        Example: (2, [{'id': '2', 'name': 'bar', 'age': 21, 'status': 1}, {
                  'id': '3', 'name': 'baz', 'age': 22, 'status': 1}])

        """
        def fn(match):
            name = match.group(1)
            if fill_with_repr:
                return f"'{kwds[name]}'" if name in kwds else match.group(0)
            return f'{kwds[name]}' if name in kwds else match.group(0)

        self.sql = self.pattern.sub(fn, self.sql)
        return self

    def fill_map(self, fill_with_repr: bool = True, map: Mapping = {}):
        """
        - `fill_with_repr`，表示是否保留字符串的引号，防止字符串参数按照整数查询(如'1')或报错('a')，默认True
        """
        return self.fill(fill_with_repr=fill_with_repr, **map)

    async def execute(self) -> tuple[int, list[dict[Any, Any]]]:
        """execute sql, not as a decorator

        Returns:
            tuple[int, list[dict[Any, Any]]]: same as sql decorator's result
        """

        async def func(): ...

        return await self(func)()

    def __call__(
        self, func: Callable[P, Coroutine[Any, Any, None | tuple[int, list[dict]]]]
    ) -> Callable[P, Coroutine[Any, Any, tuple[int, list[dict]]]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwds: P.kwargs):
            func_params_dict = get_func_params_dict(func, *args, **kwds)
            # 是否保留字符串的引号
            fill_with_repr = func_params_dict.pop('fill_with_repr', True)
            if fill_with_repr:
                self.sql = self.pattern.sub(
                    lambda m: '{'+f'{m.group(1)}!r'+'}', self.sql)
            self.sql = self.sql.format_map(func_params_dict)
            rows, resp = await Tortoise.get_connection(self.connection_name).execute_query(self.sql)
            if self.is_sqlite:
                resp = list(map(dict, resp))
            return rows, [parse_execute_res(i) for i in resp]

        return cast(Callable[P, Coroutine[Any, Any, tuple[int, list[dict]]]], wrapper)


class Select(Sql):
    """Extends Sql. \n
    Execute raw sql, return None | BaseModel_instance | list[BaseModel_instance] | list[dict]
    - 被装饰的函数/方法有个参数：`fill_with_repr`，表示是否保留字符串的引号，防止字符串参数按照整数查询(如'1')或报错('a')，默认True
    >>> Example

    ```python
    class User(BaseModel):
        id: str
        name: str
        age: int

    @Select('select * from user where id={id}')
    async def get_user_by_id(id: str) -> User|None:...

    # call in async function
    # await get_user_by_id('1')      # can also be a keyword param like id='1'
    # the result will be like User(id='1', name='foo', age=20) or None


    # ----------------------------------------------------------------------------------

    @dataclass
    class UserDTO:
        agegt: int

    @Repository
    class Bar:
        @Select('select * from user where age>{dto.agegt}')
        async def query_users(self, dto: UserDTO) -> list[User]:...

    # call in async function
    # await Inject(Bar).query_users(UserDTO(20))
    # the result will be like [User(id='2', name='bar', age=21), User(id='3', name='baz', age=22)] or []

    # ----------------------------------------------------------------------------------
    # the return value's type will be list[dict] if the return annotation is None, just like Sql decorator
    ```
    First, let T = TypeVar('T', bounds=BaseModel)

    | return annotation |  return value  |
    |       :--:        |      :--:      |
    |         T         |     T|None     |
    |      list[T]      |     list[T]    |
    |  None|list[dict]  |    list[dict]  |

    """

    @overload
    async def execute(self, expect: type[PM]) -> PM | None: ...
    @overload
    async def execute(self, expect: type[TM]) -> TM | None: ...

    @overload
    async def execute(self, expect: type[Sequence[PM]]) -> list[PM]: ...
    @overload
    async def execute(self, expect: type[Sequence[TM]]) -> list[TM]: ...

    @overload
    async def execute(self, expect: None |
                      type[Sequence[dict]] = None) -> list[dict]: ...

    async def execute(
        self, expect: type[PM] | type[Sequence[PM]] | type[TM] | type[Sequence[TM]] | None | type[Sequence[dict]] = None
    ) -> PM | TM | None | list[PM] | list[TM] | list[dict]:
        async def func(): ...

        setattr(func, '__annotations__', {'return': expect})
        return await self(func)()

    @overload
    def __call__(self, func: Callable[P, Coroutine[Any, Any, PM]]) -> Callable[P,
                                                                               Coroutine[Any, Any, PM | None]]: ...

    @overload
    def __call__(self, func: Callable[P, Coroutine[Any, Any, TM]]) -> Callable[P,
                                                                               Coroutine[Any, Any, TM | None]]: ...

    @overload
    def __call__(self, func: Callable[P, Coroutine[Any, Any, list[PM]]]) -> Callable[P,
                                                                                     Coroutine[Any, Any, list[PM]]]: ...

    @overload
    def __call__(self, func: Callable[P, Coroutine[Any, Any, list[TM]]]) -> Callable[P,
                                                                                     Coroutine[Any, Any, list[TM]]]: ...

    @overload
    def __call__(
        self, func: Callable[P, Coroutine[Any, Any, None | list[dict]]]
    ) -> Callable[P, Coroutine[Any, Any, list[dict]]]: ...

    def __call__(
        self,
        func: Callable[P, Coroutine[Any, Any, PM | list[PM] | TM | list[TM] | list[dict] | None]] | None,
    ) -> Callable[P, Coroutine[Any, Any, PM | list[PM] | TM | list[TM] | list[dict] | None]]:
        anno = func.__annotations__.get('return')
        super_class = super()

        @wraps(func)  # type: ignore
        async def wrapper(*args: P.args, **kwds: P.kwargs):
            # type: ignore
            lines, resp = await super_class.__call__(func)(*args, **kwds)
            if anno is None:
                return resp
            elif get_origin(anno) is list:
                arg = get_args(anno)[0]
                return [arg(**i) for i in resp]
            else:
                if lines > 1:
                    warn(
                        f'The number of result is {lines}, but the expected type is "{anno.__name__}", so only the first result will be returned'
                    )
                return anno(**resp[0]) if len(resp) > 0 else None

        return wrapper


class Insert(Sql):
    """
    - 被装饰的函数/方法有个参数：`fill_with_repr`，表示是否保留字符串的引号，防止字符串参数按照整数查询(如'1')或报错('a')，默认True
    >>> Example

    ```python

    @Delete('delete from user where id={id}')
    async def del_user_by_id(id: str):...

    # call in async function
    # await del_user_by_id('1')      # can also be a keyword param like id='1'
    # the result will be like 1 or 0


    @Repository
    class Bar:
        @Update('update user set age=age+1 where name={name}')
        async def update_user(self, name: str) -> int:...

    # call in async function
    # await Inject(Bar).update_user('foo')
    # the result will be like 1 or 0

    """

    async def execute(self):
        """execute sql without decorated function

        >>> Exampe

        ```python
        rows: int = await Insert('insert into {user} values("foo", 20, 1)).fill(user=UserDO.Meta.table).execute()
        ```

        """

        async def func(): ...

        return await self(func)()

    def __call__(self, func: Callable[P, Coroutine[Any, Any, None | int]]) -> Callable[P, Coroutine[Any, Any, int]]:
        super_class = super()

        @wraps(func)
        async def wrapper(*args: P.args, **kwds: P.kwargs) -> int:
            # type: ignore
            return (await super_class.__call__(func)(*args, **kwds))[0]

        return wrapper


class Update(Insert):
    """
    - 被装饰的函数/方法有个参数：`fill_with_repr`，表示是否保留字符串的引号，防止字符串参数按照整数查询(如'1')或报错('a')，默认True
    """
    ...


class Delete(Insert):
    """
    - 被装饰的函数/方法有个参数：`fill_with_repr`，表示是否保留字符串的引号，防止字符串参数按照整数查询(如'1')或报错('a')，默认True
    """
    ...
