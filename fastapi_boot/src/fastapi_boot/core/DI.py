from collections.abc import Callable
from inspect import Parameter, _empty, signature, isclass
import inspect
from typing import Annotated, Any, TypeVar, get_args, get_origin, overload
from .const import dep_store
from .model import InjectFailException

T = TypeVar('T')


def inject_params_deps(params: list[Parameter]):
    """

    Args:
        params (list[Parameter]): params

    Raises:
        InjectFailException: _description_

    Returns:
        _type_: _description_
    """
    position_params = []
    keyword_params = {}

    def add_param(param: Parameter, value: Any):
        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            position_params.append(value)
        else:
            keyword_params[param.name] = value

    for param in params:
        # 1. 有默认值
        if param.default != _empty:
            add_param(param, param.default)
        else:
            # 2. 无默认值
            # 2.1 没有类型注解
            if param.annotation == _empty:
                raise InjectFailException(f'缺少参数 "{param.name}" 的类型或默认值.')
            # 2.2. 有默认值
            # 2.2.1. 默认值是Annotated，根据type + name 注入依赖
            if get_origin(param.annotation) == Annotated:
                tp, name, *_ = get_args(param.annotation)
                add_param(param, dep_store.inject_dep(tp, name))
            else:
                # 2.2.2 其他类型，只根据type注入依赖
                add_param(param, dep_store.inject_dep(param.annotation, None))
    return position_params, keyword_params


def create_instance(cls: type[T]) -> T:
    old_params = list(signature(cls.__init__).parameters.values())[1:]  # omit self
    new_params = [
        i
        for i in old_params
        if i.kind not in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)
    ]  # omit *args、**kwargs
    calling_params = inject_params_deps(new_params)
    if hasattr(cls.__init__, '__globals__'):
        cls.__init__.__globals__.update({cls.__name__: cls})
    return cls(*calling_params[0], **calling_params[1])


@overload
def Injectable(class_or_name: str, /) -> Callable[[type[T]], type[T]]: ...


@overload
def Injectable(class_or_name: type[T], /) -> type[T]: ...


def Injectable(class_or_name: str | type[T], /):
    """
    # Example
    ```python
    @Injectable
    class Foo:...

    @Injectable('bar1')
    class Bar:...
    ```

    """
    if isclass(class_or_name):
        dep_store.add_dep(class_or_name, None, create_instance(class_or_name))
        return class_or_name
    else:

        def wrapper(cls: type[T], /):
            dep_store.add_dep(cls, class_or_name, create_instance(cls))
            return cls

        return wrapper
