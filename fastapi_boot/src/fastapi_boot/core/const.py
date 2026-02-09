from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Generic, Literal, Self, TypeVar
from warnings import warn
from fastapi import FastAPI


from .model import InjectFailException

T = TypeVar('T')


class PropNameConstant:
    # 启动时
    # use_middleware属性名
    USE_MIDDLEWARE: Literal['fastapi_boot__use_middleware_prop_name'] = (
        'fastapi_boot__use_middleware_prop_name'
    )
    # controller中route record属性名
    CONTROLLER_ROUTE_RECORD: Literal[
        'fastapi_boot__controller_route_record_prop_name'
    ] = 'fastapi_boot__controller_route_record_prop_name'

    # 请求时
    # use_dep添加的依赖在endpoint中的参数名前缀
    USE_DEP_PARAM_PREFIX_IN_ENDPOINT: Literal[
        'fastapi_boot__use_dep_param_prefix_in_endpoint'
    ] = 'fastapi_boot__use_dep_param_prefix_in_endpoint'


class UseMiddlewareReturnValuePlaceholder: ...


@dataclass
class DepStore(Generic[T]):
    # {type: instance}
    type_deps: dict[type[T], T] = field(default_factory=dict)
    # {type: {name: instance}}
    name_deps: dict[type[T], dict[str, T]] = field(default_factory=dict)

    def add_dep_by_type(self, tp: type[T], ins: T):
        if tp in self.type_deps:
            warn(f'类型为"{tp.__name__}"的依赖已存在，将被替换')
        self.type_deps[tp] = ins

    def add_dep_by_name(self, tp: type[T], name: str, ins: T):
        name_dict = self.name_deps.setdefault(tp, {})
        if name in name_dict:
            warn(f'类型为"{tp.__name__}"且名为"{name}"的依赖已存在，将被替换')
        else:
            name_dict[name] = ins

    def add_dep(self, tp: type[T], name: str | None, ins: T):
        if name is None:
            self.add_dep_by_type(tp, ins)
        else:
            self.add_dep_by_name(tp, name, ins)

    def inject_dep(self, tp: type[T], name: str | None):
        if name is None:
            dep = self.type_deps.get(tp)
        else:
            dep = self.name_deps.get(tp, {}).get(name)
        if dep is None:
            name_info = f'且名为{name}' if name is not None else ''
            raise InjectFailException(f'类型为{tp}{name_info}的依赖未找到')
        return dep

    def clear(self):
        self.type_deps.clear()
        self.name_deps.clear()


dep_store = DepStore()


# Depends被dataclass frozen了，不能加prefix数据了
@dataclass
class UseDepRecordStore:
    record: set[Any] = field(default_factory=set)

    def add(self, tp: Any):
        self.record.add(id(tp))

    def has(self, tp: Any):
        # 防止判断一些不可hash的变量
        return id(tp) in self.record


use_dep_record_store = UseDepRecordStore()


APPTask = Callable[[FastAPI], None]


@dataclass
class APPTaskStore:
    tasks: defaultdict[int, list[APPTask]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def add(self, key: int, task: APPTask) -> Self:
        self.tasks[key].append(task)
        return self

    def emit(self, key: int, app: FastAPI) -> Self:
        for task in self.tasks[key]:
            task(app)
        return self

    def clear(self):
        self.tasks.clear()


app_task_store = APPTaskStore()
