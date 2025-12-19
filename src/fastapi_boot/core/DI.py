from collections.abc import Callable
from inspect import Parameter, _empty, signature, isclass
import time
from typing import Annotated, TypeVar, cast, get_args, get_origin, no_type_check, overload

from .const import dep_store, app_store, task_store
from .model import DependencyNotFoundException, InjectFailException, AppRecord
from .utils import get_call_filename, is_position_only_param

T = TypeVar('T')


def _inject(app_record: AppRecord, tp: type[T], name: str | None) -> T:
    """inject dependency by type or name

    Args:
        app_record (AppRecord)
        tp (type[T])
        name (str | None)

    Returns:
        T: instance
    """
    start = time.time()

    def raise_func():
        name_info = f"名为 '{name}' " if name is not None else ''
        raise DependencyNotFoundException(
            f"类型为 '{tp}' {name_info}的依赖未找到")
    while True:
        if res := dep_store.inject_dep(tp, name):
            return res
        # 没找到，不扫描
        if not app_record.should_scan:
            raise_func()
        time.sleep(app_record.inject_retry_step)
        if time.time() - start > app_record.inject_timeout:
            name_info = f"名为 '{name}' " if name is not None else ''
            raise DependencyNotFoundException(
                f"类型为 '{tp}' {name_info}的依赖未找到")


def inject_params_deps(app_record: AppRecord, params: list[Parameter]):
    """解析参数，注入依赖
    Args:
        params (list[Parameter]): 参数列表
    """
    position_params = []
    kw_params = {}
    for param in params:
        # 1. with default
        if param.default != _empty:
            if is_position_only_param(param):
                position_params.append(param.default)
            else:
                kw_params.update({param.name: param.default})
        else:
            # 2. with default
            if param.annotation == _empty:
                # 2.1 no annotation
                raise InjectFailException(
                    f'The annotation of param {param.name} is missing, add an annotation or give it a default value'
                )
            # 2.2. with Annotated, has type and name
            if get_origin(param.annotation) == Annotated:
                tp, name, *_ = get_args(param.annotation)
                ins = _inject(app_record, tp, name)
                if is_position_only_param(param):
                    position_params.append(ins)
                else:
                    kw_params.update({param.name: ins})
            else:
                # 2.2.2 only type, no name
                ins = _inject(app_record, param.annotation, None)
                if is_position_only_param(param):
                    position_params.append(ins)
                else:
                    kw_params.update({param.name: ins})
    return position_params, kw_params


# ------------------------------------------------------- Bean ------------------------------------------------------- #


def collect_bean(app_record: AppRecord, func: Callable, name: str | None = None):
    """
    1. run function decorated by Bean decorator
    2. add the result to deps_store

    Args:
        func (Callable): func
        name (str | None, optional): name of dep
    """
    params = list(signature(func).parameters.values())
    return_annotations = signature(func).return_annotation
    calling_params = inject_params_deps(app_record, params)
    instance = func(*calling_params[0], **calling_params[1])
    tp = return_annotations if return_annotations != _empty else type(instance)
    dep_store.add_dep(tp, name, instance)


@overload
def Bean(func_or_name: str): ...


@overload
def Bean(func_or_name: Callable[..., T]): ...


@no_type_check
def Bean(func_or_name: str | Callable[..., T]) -> Callable[..., T]:
    """A decorator, will collect the return value of the func decorated by Bean
    # Example
    1. collect by `type`
    ```python
    @dataclass
    class Foo:
        bar: str

    @Bean
    def _():
        return Foo('baz')
    ```

    2. collect by `name`
    ```python
    class User(BaseModel):
        name: str = Field(max_length=20)
        age: int = Field(gt=0)

    @Bean('user')
    def _():
        return User(name='zs', age=20)

    @Bean('user2)
    def _():
        return User(name='zs', age=21)
    ```
    """
    filename = get_call_filename()
    if callable(func_or_name):
        task_store.schedule(
            filename, lambda app_record: collect_bean(app_record, func_or_name))
        return func_or_name
    else:
        def wrapper(func: Callable[..., T]):
            task_store.schedule(filename, lambda app_record: collect_bean(
                app_record, func, func_or_name))
            return func
        return wrapper


# ---------------------------------------------------- Injectable ---------------------------------------------------- #
def inject_init_deps_and_get_instance(app_record: AppRecord, cls: type[T]) -> T:
    """_inject cls's __init__ params and get params deps"""
    old_params = list(signature(cls.__init__).parameters.values())[1:]  # self
    new_params = [
        i for i in old_params if i.kind not in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)
    ]  # *args、**kwargs
    calling_params = inject_params_deps(app_record, new_params)
    return cls(*calling_params[0], **calling_params[1])


def collect_dep(app_record: AppRecord, cls: type, name: str | None = None):
    """init class decorated by Inject decorator and collect it's instance as dependency"""
    if hasattr(cls.__init__, '__globals__'):
        cls.__init__.__globals__[cls.__name__] = cls  # type: ignore
    instance = inject_init_deps_and_get_instance(app_record, cls)
    dep_store.add_dep(cls, name, instance)


@overload
def Injectable(class_or_name: str) -> Callable[[type[T]], type[T]]: ...


@overload
def Injectable(class_or_name: type[T]) -> type[T]: ...


def Injectable(class_or_name: str | type[T]):
    """decorate a class and collect it's instance as a dependency
    # Example
    ```python
    @Injectable
    class Foo:...

    @Injectable('bar1')
    class Bar:...
    ```

    """
    filename = get_call_filename()
    if isclass(class_or_name):
        task_store.schedule(filename, lambda app_record: collect_dep(
            app_record, class_or_name))
        return class_or_name
    else:

        def wrapper(cls: type[T]):
            task_store.schedule(filename, lambda app_record: collect_dep(
                app_record, cls, class_or_name))
            return cls

        return cast(Callable[[type[T]], type[T]], wrapper)


# ------------------------------------------------------ Inject ------------------------------------------------------ #
class AtUsable(type):
    """support @"""

    def __matmul__(self, other: type[T]) -> T:
        filename = get_call_filename()
        return _inject(app_store.get_or_raise(filename), other, cast(type[Inject], self).latest_named_deps_record.get(filename))

    def __rmatmul__(self, other: type[T]) -> T:
        filename = get_call_filename()
        return _inject(app_store.get_or_raise(filename), other, cast(type[Inject], self).latest_named_deps_record.get(filename))


class Inject(metaclass=AtUsable):
    """注入依赖
    >>> Example

    - inject by **type**
    ```python
    a = Inject(Foo)
    b = Inject @ Foo
    c = Foo @ Inject

    @Injectable
    class Bar:
        a = Inject(Foo)
        b = Inject @ Foo
        c = Foo @ Inject

        def __init__(self, ia: Foo, ic: Foo):
            self.ia = ia
            self.ib = Inject @ Foo
            self.ic = ic
    ```

    - inject by **type** and **name**
    ```python
    a = Inject(Foo, 'foo1')
    b = Inject.Qualifier('foo2') @ Foo
    c = Foo @ Inject.Qualifier('foo3')

    @Injectable
    class Bar:
        a = Inject(Foo, 'foo1')
        b = Inject.Qualifier('foo2') @ Foo
        c = Foo @ Inject.Qualifier('foo3')

        def __init__(self, ia: Annotated[Foo, 'foo1'], ic: Annotated[Foo, 'foo3']):
            self.ia = ia
            self.ib = Inject.Qualifier('foo2') @ Foo
            self.ic = ic
    ```
    """

    latest_named_deps_record: dict[str, str | None] = {}

    def __new__(cls, tp: type[T], name: str | None = None) -> T:
        """Inject(Type, name = None)"""
        filename = get_call_filename()
        cls.latest_named_deps_record.update({filename: name})
        res = _inject(app_store.get_or_raise(filename), tp, name)
        cls.latest_named_deps_record.update({filename: None})  # set name None
        return res

    @classmethod
    def Qualifier(cls, name: str):
        """Inject.Qualifier(name)"""
        filename = get_call_filename()
        cls.latest_named_deps_record.update({filename: name})
        return cls
