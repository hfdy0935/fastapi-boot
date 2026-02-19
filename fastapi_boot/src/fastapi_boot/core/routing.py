from collections.abc import Callable, Sequence
from enum import Enum
from functools import reduce, wraps
from inspect import Parameter, getmembers, iscoroutinefunction, signature
from typing import Any, TypeVar

from fastapi import APIRouter, Response, params, WebSocket as FastAPIWebSocket
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, Lifespan

from fastapi_boot.core.DI import create_injectable_instance

from .const import (
    PropNameConstant,
    UseMiddlewareReturnValuePlaceholder,
    app_task_store,
    use_dep_record_store,
)
from .model import (
    BaseHttpRouteItem,
    BaseHttpRouteItemWithoutEndpoint,
    EndpointRouteRecord,
    LowerHttpMethod,
    PrefixRouteRecord,
    UseMiddlewareRecord,
)
from .model import SpecificHttpRouteItemWithoutEndpointAndMethods as SM
from .model import WebSocketRouteItem, WebSocketRouteItemWithoutEndpoint


T = TypeVar('T', bound=Callable)
RouterCls = TypeVar('RouterCls')


# ---------------------------------------------------- Controller ---------------------------------------------------- #


def get_use_result(cls: type[RouterCls]):
    """获取controller的use_xxx配置

    Args:
        cls (type[RouterCls]): _description_

    Returns:
        _type_: _description_
    """
    use_dep_dict = {}
    cls_anno: dict = cls.__dict__.get('__annotations__', {})
    use_middleware_records: list[UseMiddlewareRecord] = []
    for k, v in getmembers(cls):
        if use_dep_record_store.has(v):
            use_dep_dict[k] = (cls_anno.get(k), v)
        elif (
            isinstance(v, UseMiddlewareReturnValuePlaceholder)
            and (attr := getattr(v, PropNameConstant.USE_MIDDLEWARE))
            and isinstance(attr, UseMiddlewareRecord)
        ):
            use_middleware_records.append(attr)
    return use_dep_dict, use_middleware_records


def trans_endpoint(
    instance: Any,
    endpoint: Callable,
    use_dep_dict: dict,
    use_middleware_records: list[UseMiddlewareRecord],
):
    """
    处理endpoint，添加use_dep依赖、替换self、替换websocket

    :param instance: 被Controller装饰的类的实例
    :type instance: Any
    :param endpoint: endpoint
    :type endpoint: Callable
    :param use_dep_dict: use_dep_dict
    :type use_dep_dict: dict
    :param use_middleware_records: use_middleware_records
    :type use_middleware_records: list[UseMiddlewareRecord]
    """
    params: list[Parameter] = list(signature(endpoint).parameters.values())
    has_self = params[0].name == 'self' if params else False
    if has_self:
        params.pop(0)

    # add use_dep's deps
    for k, v in use_dep_dict.items():
        req_name = f'{PropNameConstant.USE_DEP_PARAM_PREFIX_IN_ENDPOINT}_{k}'
        params.append(
            Parameter(
                name=req_name,
                kind=Parameter.KEYWORD_ONLY,
                annotation=v[0],
                default=v[1],
            )
        )
    # replace endpoint

    @wraps(endpoint)
    async def new_endpoint(*args, **kwargs):
        for k, v in use_dep_dict.items():
            req_name = f'{PropNameConstant.USE_DEP_PARAM_PREFIX_IN_ENDPOINT}_{k}'
            setattr(instance, k, kwargs.pop(req_name))
            kwargs.get(req_name)
        for k, v in kwargs.items():
            if isinstance(v, FastAPIWebSocket):
                for record in use_middleware_records:
                    record.add_ws_middleware(v)
        new_args = (instance, *args) if has_self else args
        if iscoroutinefunction(endpoint):
            return await endpoint(*new_args, **kwargs)
        else:
            return endpoint(*new_args, **kwargs)

    setattr(
        new_endpoint,
        '__signature__',
        signature(new_endpoint).replace(parameters=params),
    )
    return new_endpoint


def resolve_endpoint(
    anchor: APIRouter,
    api_route: EndpointRouteRecord,
    instance: Any,
    use_deps_dict: dict,
    prefix: str,
    use_middleware_records: list[UseMiddlewareRecord],
):
    """
    处理endpoint，http中间件

    :param anchor: 说明
    :type anchor: APIRouter
    :param api_route: 说明
    :type api_route: EndpointRouteRecord
    :param instance: 说明
    :type instance: Any
    :param use_deps_dict: 说明
    :type use_deps_dict: dict
    :param prefix: 说明
    :type prefix: str
    :param use_middleware_records: 说明
    :type use_middleware_records: list[UseMiddlewareRecord]
    """
    path = prefix + api_route.record.path
    # http
    if isinstance(api_route.record, BaseHttpRouteItem):
        urls_methods = [(path, method.upper()) for method in api_route.record.methods]
        for r in use_middleware_records:
            r.http_urls_methods.extend(urls_methods)
    new_endpoint = trans_endpoint(
        instance, api_route.record.endpoint, use_deps_dict, use_middleware_records
    )
    path_in_controller = '/'.join(path.split('/')[2:])
    if path_in_controller != '':
        path_in_controller = '/' + path_in_controller
    api_route.record.replace_endpoint(new_endpoint).replace_path(
        path_in_controller
    ).mount_to(anchor)


def resolve_class_based_view(
    anchor: APIRouter,
    route_record: PrefixRouteRecord[RouterCls],
    prefix: str,
    controller_id: int,
):
    """
    resolve_class_based_view

    :param anchor: 说明
    :type anchor: APIRouter
    :param route_record: 说明
    :type route_record: PrefixRouteRecord[RouterCls]
    :param prefix: 说明
    :type prefix: str
    :param controller_id: 说明
    :type controller_id: str

    """
    cls: type[RouterCls] = route_record.cls
    use_deps_dict, use_middleware_records = get_use_result(cls)
    instance: RouterCls = create_injectable_instance(cls)
    new_prefix = prefix + route_record.prefix

    for v in vars(cls).values():
        if hasattr(v, PropNameConstant.CONTROLLER_ROUTE_RECORD) and (
            attr := getattr(v, PropNameConstant.CONTROLLER_ROUTE_RECORD)
        ):
            if isinstance(attr, EndpointRouteRecord):
                resolve_endpoint(
                    anchor,
                    attr,
                    instance,
                    use_deps_dict,
                    new_prefix,
                    use_middleware_records,
                )
            elif isinstance(attr, PrefixRouteRecord):
                resolve_class_based_view(anchor, attr, new_prefix, controller_id)
    # add http middleware
    if use_middleware_records:
        app_task_store.add(
            controller_id,
            lambda app: reduce(
                lambda a, b: a + b, use_middleware_records
            ).add_http_middleware(app),
        )


class Controller(APIRouter):
    def __init__(
        self,
        prefix: str = '',
        *,
        tags: list[str | Enum] | None = None,
        dependencies: Sequence[params.Depends] | None = None,
        default_response_class: type[Response] = Default(JSONResponse),
        responses: dict[int | str, dict[str, Any]] | None = None,
        callbacks: list[BaseRoute] | None = None,
        routes: list[BaseRoute] | None = None,
        redirect_slashes: bool = True,
        default: ASGIApp | None = None,
        dependency_overrides_provider: Any | None = None,
        route_class: type[APIRoute] = APIRoute,
        on_startup: Sequence[Callable[[], Any]] | None = None,
        on_shutdown: Sequence[Callable[[], Any]] | None = None,
        lifespan: Lifespan[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id
        ),
    ):
        super().__init__(
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            default_response_class=default_response_class,
            responses=responses,
            callbacks=callbacks,
            routes=routes,
            redirect_slashes=redirect_slashes,
            default=default,
            dependency_overrides_provider=dependency_overrides_provider,
            route_class=route_class,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            generate_unique_id_function=generate_unique_id_function,
        )

    def __call__(self, cls: type[RouterCls]) -> type[RouterCls]:
        resolve_class_based_view(self, PrefixRouteRecord(cls, self.prefix), '', id(cls))
        app_task_store.add(id(cls), lambda app: app.include_router(self))
        return cls

    def __getattribute__(self, k: str):
        attr = super().__getattribute__(k)
        if k in [*LowerHttpMethod, 'api_route', 'websocket', 'websocket_route']:

            def decorator(*args, **kwds):
                def wrapper(endpoint):
                    # @Controller(...).websocket(...)  @Controller(...).websocket_route(...)
                    if k in ['websocket', 'websocket_route']:
                        WebSocketRouteItem(endpoint, *args, **kwds).mount_to(self)
                    elif k == 'api_route':
                        BaseHttpRouteItem(endpoint, *args, **kwds).mount_to(self)
                    else:
                        BaseHttpRouteItem(
                            endpoint, methods=[k], *args, **kwds
                        ).mount_to(self)
                    app_task_store.add(
                        id(endpoint), lambda app: app.include_router(self)
                    )
                    return endpoint

                return wrapper

            return decorator
        return attr


# ------------------------------------------------------Request Mapping ----------------------------------------------------- #


class Req(BaseHttpRouteItemWithoutEndpoint):
    def __call__(self, endpoint: T) -> T:
        route_item = BaseHttpRouteItem(endpoint=endpoint, **self.dict).format_methods()
        # 顶层
        if len(endpoint.__qualname__.split('.')) == 1:
            app_task_store.add(id(endpoint), lambda app: route_item.mount_to(app))
        else:
            # 作为Controller的方法
            route_record = EndpointRouteRecord(route_item)
            setattr(endpoint, PropNameConstant.CONTROLLER_ROUTE_RECORD, route_record)
        return endpoint


class Get(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict)(endpoint)


class Post(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['POST'])(endpoint)


class Put(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['PUT'])(endpoint)


class Delete(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['DELETE'])(endpoint)


class Head(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['HEAD'])(endpoint)


class Patch(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['PATCH'])(endpoint)


class Trace(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['TRACE'])(endpoint)


class Options(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['OPTIONS'])(endpoint)


class WebSocket(WebSocketRouteItemWithoutEndpoint):
    def __call__(self, endpoint: T) -> T:
        route_item = WebSocketRouteItem(endpoint=endpoint, **self.dict)
        # 顶层
        if len(endpoint.__qualname__.split('.')) == 1:
            app_task_store.add(id(endpoint), lambda app: route_item.mount_to(app))
        else:
            # 作为Controller的方法
            route_record = EndpointRouteRecord(route_item)
            setattr(endpoint, PropNameConstant.CONTROLLER_ROUTE_RECORD, route_record)
        return endpoint


# ------------------------------------------------------ Prefix ------------------------------------------------------ #
C = TypeVar('C')


def Prefix(prefix: str = ""):
    """Controller中的隔离块
    >>> Example
    ```python
    def f1(p: str = Query()):
        return 'f1'
    def f2(q: int = Query()):
        return 'f2'

    @Controller()
    class UserController:
        p = use_dep(f1)

        @Prefix()
        class Foo:
            q = use_dep(f2)
            @Get()
            def get_user(self): # only need the query param 'q'
                return self.q
    ```
    """

    def wrapper(cls: type[C]) -> type[C]:
        prefix_route_record = PrefixRouteRecord(cls=cls, prefix=prefix)
        setattr(cls, PropNameConstant.CONTROLLER_ROUTE_RECORD, prefix_route_record)
        return cls

    return wrapper
